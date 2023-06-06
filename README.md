# thesis-knowledge-graph
Create a knowledge graph construction tool for AWS system vulnerability analysis

In order for this tool to work, one has to have an AWS profile with at least Security Audit priviledges (or Administrator Access). Also, he has to install awless and use this profile as its main profile. Trufflehog, neo4j Desktop for Ubuntu and the Cloudgoat directory must be in the same location as the main files.

The main code is the `create-graph.py` file and in order to use it, one has to run the command `python3 create-graph.py <user>`
