from neo4j import GraphDatabase
import subprocess
import json
from dict import escalation_methods
import sys

services = ['s3', 'iam', 'lambda', 'cloudwatch', 'ec2', 'InstanceProfile', 'rds']

if len(sys.argv) < 2:
    print("no user provided")
    exit()

print("running first script...")
subprocess.run(["bash", "./listall.sh"])
print("done")

name = sys.argv[1]
print("user to search for:",name )

with open('json-files/users.json', 'r') as u:
    users=json.load(u)

flag=0
for user in users:
    if user['Name'] == name:
        print("found user:", name)
        flag=1
        break
if flag==0:
    print("No such user")
    exit()    

print("running second script...")
subprocess.run(["bash", "./polattach.sh"])
print("done")

print("running third script...")
subprocess.run(["bash", "./polversions.sh"])
print("done")

with open('json-files/polattach.json', 'r') as pa:
    polats=json.load(pa)

flag=0
for element in polats:
    if not element['PolicyUsers']:
        continue  # Skip element if PolicyUsers is empty

    for user in element['PolicyUsers']:
        role_name = user.get('UserName')
        if role_name != name:
            continue
        else:
            desired_ID= element['ID']
            flag=1
            print("found policy for said user")
if flag==0:
    print("No policy for user", name)
else:
    matched_policies = {}
    with open('json-files/policies.json', 'r') as f:
        policies = json.load(f)


    desired_policy = None
    for policy in policies:
        if policy['ID'] == desired_ID:
            desired_policy = policy
            break

    if desired_policy:
        document = json.loads(desired_policy['Document'])
        statements = document['Statement']
    policy_actions = set()
    for statement in statements:
        if 'Action' in statement:
            actions = statement['Action']
            if isinstance(actions, str):
                policy_actions.add(actions)
            else:
                policy_actions |= set(actions)

    for key, value in escalation_methods.items():
        if all(a in policy_actions for a in value.keys()):
            matched_policies[key] = set(value.keys())

    matched_policies_list = [{'ID': f"method{i+1}", 'Name': key, 'User': name, 'Permissions': list(value)} 
                             for i, (key, value) in enumerate(matched_policies.items())]

    with open('json-files/escalation_methods.json', 'w') as f:
        json.dump(matched_policies_list, f, indent=2)
        
    print("escalation_methods file created successfully!")

print("searching for credentials in lambdas and s3objects")
subprocess.run(["bash", "./searchcred.sh"])
print("done")

driver = GraphDatabase.driver("bolt://localhost:7689", auth=("User", "Pass"), encrypted=False) #7687 was taken, add your database user/pass in auth
session=driver.session()

#delete old parts
q0="""
match (n)
detach delete n
"""
session.run(q0)


with open('json-files/polattach.json', 'r') as f:
    content = f.read().strip()
if content == "[]":
    print("No attachments")
else:
    #basic policyattachment nodes with arns
    q1="""
    CALL apoc.load.json("json-files/polattach.json") YIELD value
    UNWIND value AS attachment
    MERGE (pa:PolicyAttachment {id: attachment.ID})
    SET pa.arn = attachment.Arn
    """
    session.run(q1)

    #add to them policy roles part
    q2="""
    CALL apoc.load.json("json-files/polattach.json") YIELD value
    UNWIND value AS attachment
    unwind attachment.PolicyRoles as polroles
    MERGE (pa:PolicyAttachment {id: attachment.ID})
    Set pa.roleattachedname = polroles.RoleName
    set pa.roleattachedid = polroles.RoleId
    """
    session.run(q2)

    #add to them policy users part
    q3="""
    CALL apoc.load.json("json-files/polattach.json") YIELD value
    UNWIND value AS attachment
    unwind attachment.PolicyUsers as polusers
    MERGE (pa:PolicyAttachment {id: attachment.ID})
    Set pa.userattachedname = polusers.UserName
    set pa.userattachedid = polusers.UserId
    """
    session.run(q3)

#placeholder, can and should add policy groups part

#create user nodes
with open('json-files/users.json', 'r') as u:
    users=json.load(u)

if users is None:
    print ("no users")
else:
    q4="""
    CALL apoc.load.json("json-files/users.json") YIELD value
    unwind value as u
    create (:User {id: u.ID, name: u.Name, arn: u.Arn})
    """
    session.run(q4)

#create policy nodes
with open('json-files/policies.json', 'r') as f:
    content = f.read().strip()
if content == "[]":
    print("No policies")
else:
    #extra pragma, na balw mia idiothta pou na deixnei eukola me ti paizei to ka8e policy
    policies = json.loads(content)
    for policy in policies:
        document = policy['Document']
        can_work_with = []
        for service in services:
            if service in document:
                can_work_with.append(service)
        if can_work_with:
            policy['CanWorkWith'] = json.dumps(can_work_with)
    
    with open('json-files/policies.json', 'w') as f:
        f.write(json.dumps(policies))

    q5="""
    CALL apoc.load.json("json-files/policies.json") YIELD value
    unwind value as p
    create (:Policy {id: p.ID, name: p.Name, arn: p.Arn, type: p.Type, document: p.Document, canworkwith: p.CanWorkWith})

    """
    session.run(q5)

#create role nodes
with open('json-files/roles.json', 'r') as f:
    content = f.read().strip()
if content == "[]":
    print("No roles")
else:
    q6="""
    CALL apoc.load.json("json-files/roles.json") YIELD value
    unwind value as r
    create (:Role {id: r.ID, name: r.Name, arn: r.Arn, trustpolicy: r.TrustPolicy})
    """
    session.run(q6)

#relationship between policys and policy attachments
q7="""
match(p:Policy), (pa:PolicyAttachment)
where p.id = pa.id
create (p)-[:HAS_ATTACHMENT]->(pa)
"""
session.run(q7)

#relationship between roles and policy attachments
q8="""
match(r:Role), (pa:PolicyAttachment)
where r.id = pa.roleattachedid
create (pa)-[:Role_ATTACHED]->(r)
"""
session.run(q8)

#relationship between users and policy attachments
q9="""
match(u:User), (pa:PolicyAttachment)
where u.name = pa.userattachedname
create (pa)-[:USED_BY_USER]->(u)
"""
session.run(q9)


#add an if the file instances.json file is not null
#create instances nodes
with open('json-files/instances.json', 'r') as ins:
    instances=json.load(ins)

if instances is None:
    print ("no instances")
else:
    q10="""
    CALL apoc.load.json("json-files/instances.json") YIELD value
    UNWIND value AS instances
    MERGE (ins:Instance {id: instances.ID})
    SET ins.name = instances.Name
    SET ins.image = instances.Image
    SET ins.securitygroups = instances.SecurityGroups
    SET ins.architecture = instances.Architecture
    SET ins.privateip = instances.PrivateIP
    set ins.publicip = instances.PublicIP
    set ins.networkinterfaces = instances.NetworkInterfaces
    set ins.state = instances.State
    set ins.subnet = instances.Subnet
    set ins.type = instances.Type
    set ins.vpc = instances.Vpc
    set ins.tags = instances.Tags
    set ins.profile = instances.Profile
    set ins.keypair = instances.KeyPair
    """
    session.run(q10)

#add an if the file profiles.json is not null
#create instanceprofile nodes
with open('json-files/profiles.json', 'r') as profs:
    profiles=json.load(profs)

if profiles is None:
    print ("no instance profiles")
else:
    q11="""
    CALL apoc.load.json("json-files/profiles.json") YIELD value
    UNWIND value AS instprof
    create (:InstanceProfile {id: instprof.ID, name: instprof.Name, arn: instprof.Arn, roles: instprof.Roles})
    """
    session.run(q11)

#create connection between instanceprofile and roles
q12="""
match(r:Role),(inpr:InstanceProfile)
where r.id in inpr.roles
create (r)-[:BELONGS_TO]->(inpr)
"""
session.run(q12)

#create escalation_methods nodes
with open('json-files/escalation_methods.json', 'r') as esc:
    escals=json.load(esc)

if escals is None:
    print ("no methods for escalation")
else:
    q13="""
    CALL apoc.load.json("json-files/escalation_methods.json") YIELD value
    unwind value as esc
    create (:EscalationMethod {id: esc.ID, name: esc.Name, user: esc.User, permissions: esc.Permissions})
    """
    session.run(q13)

#create relationship between user and escalation techniques
q14="""
match (u:User),(esc:EscalationMethod)
where u.name = esc.user
create (u)-[:POSSIBLE_ESCALATION]->(esc)
"""
session.run(q14)


with open('json-files/polversions.json', 'r') as polv:
    versi=json.load(polv)

if versi is not None:
    q15="""
    CALL apoc.load.json("json-files/polversions.json") YIELD value
    UNWIND value AS vers
    MERGE (pv:PolicyVersion {id: vers.ID})
    SET pv.arn = vers.Arn
    """
    session.run(q15)

    q16="""
    CALL apoc.load.json("json-files/polversions.json") YIELD value
    unwind value as trial
    unwind trial.PolicyVersion as doc
    unwind doc.Document as statement
    unwind statement.Statement as action2
    MERGE (pv:PolicyVersion {id: trial.ID})
    Set pv.action = action2.Action
    set pv.resource = action2.Resource
    set pv.effect= action2.Effect
    """
    session.run(q16)

    q17="""
    match(p:Policy), (pv:PolicyVersion)
    where p.arn = pv.arn
    create (p)-[:HAS_VERSION]->(pv)
    """
    session.run(q17)

q18="""
match(inst:Instance), (inprof:InstanceProfile)
where inst.profile = inprof.arn
create (inst)-[:HAS_INSTANCE_PROFILE]->(inprof)
"""
session.run(q18)

#create buckets
with open('json-files/buckets.json', 'r') as b:
    buckets=json.load(b)

if buckets is None:
    print ("no buckets")
else:
    q19="""
    CALL apoc.load.json("json-files/buckets.json") YIELD value
    UNWIND value AS buc
    MERGE (b:Bucket {id: buc.ID})
    """
    session.run(q19)

#create objects
with open('json-files/s3objects.json', 'r') as bo:
    objects=json.load(bo)

if objects is None:
    print ("no bucket objects")
else:
    q20="""
    CALL apoc.load.json("json-files/s3objects.json") YIELD value
    UNWIND value AS ob
    MERGE (obj:S3Object {id: ob.ID})
    set obj.bucket = ob.Bucket
    set obj.class = ob.Class 
    set obj.key = ob.Key
    set obj.size = ob.Size 
    set obj.Owner = ob.Owner
    set obj.hascredsfor = ob.HasCredsFor
    """
    session.run(q20)

#create relationship between buckets and objects
q21="""
match(b:Bucket), (obj:S3Object)
where b.id = obj.bucket
create (b)-[:HAS_OBJECT]->(obj)
"""
session.run(q21)

#check if some policies can access buckets, and if they do create a relationship
q22="""
MATCH (p:Policy)
WHERE p.document CONTAINS 'Resource\":\"arn:'
WITH p, apoc.convert.fromJsonMap(p.document) as document
UNWIND document.Statement as statement
WITH p, trim(split(statement.Resource, ":::")[-1]) as resource
MATCH (b:Bucket {id: resource})
CREATE (p)-[:HAS_BUCKET]->(b)
"""
session.run(q22)


#can do the same if later on policies can access other specific objects, maybe rds or lambdas

#create the rds databases nodes
with open('json-files/databases.json', 'r') as data:
    databases=json.load(data)

if databases is None:
    print ("no databases")
else:
    q23="""
    CALL apoc.load.json("json-files/databases.json") YIELD value
    UNWIND value AS databases
    MERGE (d:Database {id: databases.ID})
    SET d.arn = databases.Arn
    set d.class = databases.Class
    set d.ca = databases.CertificateAuthority
    set d.globalid = databases.Global.ID
    set d.engine = databases.Engine
    set d.engineversion = databases.EngineVersion
    set d.name = databases.Name
    set d.publicdns = databases.PublicDNS
    set d.securitygroups = databases.SecurityGroups
    set d.state = databases.State
    set d.storage = databases.Storage
    set d.username = databases.Username
    set d.zone = databases.Zone
    """
    session.run(q23)

#create lambda functions
with open('json-files/functions.json', 'r') as func:
    functions=json.load(func)

if functions is None:
    print("no functions")
else:
    q24="""
    CALL apoc.load.json("json-files/functions.json") YIELD value
    UNWIND value AS lam
    MERGE (l:Lambda {id: lam.ID})
    SET l.arn = lam.Arn
    set l.description = lam.Description
    set l.handler = lam.Handler
    set l.name = lam.Name
    set l.hash = lam.Hash
    set l.version = lam.Version
    set l.role = lam.Role
    set l.runtime = lam.Runtime
    set l.timeout = lam.Timeout
    set l.size = lam.Size
    set l.hascredsfor = lam.HasCredsFor
    """
    session.run(q24)

#relationships between roles and lambdas
q25="""
match(r:Role),(l:Lambda)
where r.arn = l.role
create (r)-[:BELONGS_TO]->(l)
"""
session.run(q25)

#create keypairs
with open('json-files/keypairs.json', 'r') as ke:
    keys=json.load(ke)

if keys is None:
    print("no keypairs")
else:
    q25="""
    CALL apoc.load.json("json-files/keypairs.json") YIELD value
    UNWIND value AS keys
    MERGE (k:Keypair {id: keys.ID})
    set k.fingerprint = keys.Fingerprint
    """
    session.run(q25)

#relationship between instances and keys
q26="""
match(k:Keypair), (inst:Instance)
where k.id = inst.keypair
create (inst)-[:HAS_KEYPAIR_OF]->(k)
"""
session.run(q26)

#if there are credentials, show for which users
q27="""
match (l:Lambda), (u:User)
where l.hascredsfor = u.name
create (l)-[:HAS_CREDENTIALS_FOR]->(u)
"""
session.run(q27)

q28="""
match (ob:S3Object), (u:User)
where ob.hascredsfor = u.name
create (ob)-[:HAS_CREDENTIALS_FOR]->(u)
"""
session.run(q28)

#if instead of credentials, i find a private key, connect with every possible keypair i have
q29="""
match (ob:S3Object), (k:Keypair)
where ob.hascredsfor = "keypair"
create (ob)-[:MIGHT_BE_PRIVATE_KEY_OF]->(k)
"""
session.run(q29)

q30="""
match (n:User)
where n.name = "cloudgoat2"
delete n
"""
session.run(q30)

# extra sto telos na deiksw gia viktor
q31="""
MATCH (p:Policy)
WITH p, p.canworkwith AS canworkwith
MATCH (n)
WHERE (n:Lambda AND canworkwith CONTAINS 'lambda')
MERGE (p)-[:CAN_WORK_WITH_LAMBDA]->(n)
"""
session.run(q31)

#two parts of the same command, for the neo4j to not crash
q32="""
MATCH (p:Policy)
WITH p, p.canworkwith AS canworkwith
MATCH (n)
WHERE n:Database AND canworkwith CONTAINS 'rds'
MERGE (p)-[:CAN_WORK_WITH_DATABASE]->(n)
"""
session.run(q32)

q33="""
MATCH (p:Policy)
WITH p, p.canworkwith AS canworkwith
MATCH (n)
WHERE n:Instance AND canworkwith CONTAINS 'ec2'
MERGE (p)-[:CAN_WORK_WITH_INSTANCE]->(n)
"""
session.run(q33)

q34="""
MATCH (p:Policy)
WITH p, p.canworkwith AS canworkwith
MATCH (n)
WHERE n:InstanceProfile AND canworkwith CONTAINS 'InstanceProfile'
MERGE (p)-[:CAN_WORK_WITH_INSTANCE_PROFILE]->(n)
"""
session.run(q34)

q35="""
MATCH (p:Policy)
WITH p, p.canworkwith AS canworkwith
MATCH (n)
WHERE n:Bucket AND canworkwith CONTAINS 's3'
MERGE (p)-[:CAN_WORK_WITH_BUCKET]->(n)
"""
session.run(q35)

#if a policy has already a bucket connected, don't show the can work with the other buckets
q36="""
MATCH (p:Policy)-[r:HAS_BUCKET]->()
WITH p
WHERE EXISTS((p)-[:HAS_BUCKET]->())
MATCH (p)-[cw:CAN_WORK_WITH_BUCKET]-()
delete cw
"""
session.run(q36)

#telos
driver.close()

