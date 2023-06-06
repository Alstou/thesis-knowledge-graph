#!/bin/bash
if [ -f json-files/polattach.json ]; then
  rm json-files/polattach.json
fi
touch json-files/polattach.json
echo "[" >> json-files/polattach.json
# # Load the JSON data into a variable
json_data=$(cat json-files/policies.json)

# Use jq to extract the value of the "Arn" key from each object
arns=$(echo "$json_data" | jq -r '.[] | .Arn')
ids=$(echo "$json_data" | jq -r '.[] | .ID')

for id in $ids; do
	ids_array+=($id)	
done

count=0
for arn in $arns; do
  output=$(aws iam list-entities-for-policy --policy-arn "$arn" --profile cloudgoat2)
  output_with_arn=$(echo "$output" | jq --arg arn "$arn" --arg id "${ids_array[$count]}" '. | {Arn: $arn, ID: $id, PolicyGroups: .PolicyGroups, PolicyUsers: .PolicyUsers, PolicyRoles: .PolicyRoles}')
  echo "$output_with_arn," >> json-files/polattach.json
  (( count++ ))
 done
# Remove the trailing comma from the last line of the file
sed -i '$s/,$//' json-files/polattach.json
echo "]" >> json-files/polattach.json

