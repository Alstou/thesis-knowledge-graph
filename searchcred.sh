#!/bin/bash

#arxikopoihseis
if [ -f json-files/lambdaconfig.json ]; then
  rm json-files/lambdaconfig.json
fi
touch json-files/lambdaconfig.json

if [ -f json-files/gourouni.txt ]; then
  rm json-files/gourouni.txt
fi
touch json-files/gourouni.txt

if [ -f json-files/objectdata.txt ]; then
  rm json-files/objectdata.txt
fi
touch json-files/objectdata.txt

#checkare an uparxei lambda file, kai an nai, koitakse tis leptomereies.
#apo8hkeuse tis leptomereies kai des an exei credentials
if jq -e '. | length == 0' json-files/functions.json > /dev/null; then
    echo "No functions to search for creds"
else
    json_data=$(cat json-files/functions.json)
    names=$(echo "$json_data" | jq -r '.[] | .Name')
    for name in $names; do
    	aws lambda get-function-configuration --function-name $name --profile cloudgoat2 > json-files/lambdaconfig.json
    	trufflehog filesystem --no-update json-files/lambdaconfig.json > json-files/gourouni.txt
    	if [ -s json-files/gourouni.txt ]; then
            creds=$(grep "Raw result" json-files/gourouni.txt)
            if echo "$creds" | grep -q "BEGIN OPENSSH PRIVATE KEY"; then
                jq --arg key "$key" --arg creds "keypair" '(.[] | select(.Key == $key)) |= .+ {"hascredsfor": $creds}' json-files/s3objects.json > temp && mv temp json-files/s3objects.json                
            else
        		creds=$(grep "Raw result" json-files/gourouni.txt  | head -n 1 | awk '{print $NF}')
        		usercreds=$(aws iam get-access-key-last-used --access-key-id $creds --profile cloudgoat2 --query 'UserName' --output text)
        		jq --arg name "$name" --arg creds "$usercreds" '(.[] | select(.Name == $name)) |= .+ {"HasCredsFor": $creds}' json-files/functions.json > temp && mv temp json-files/functions.json
		    fi
        fi
    done 
fi

#to idio edw alla me ta s3objects
if jq -e '. | length == 0' json-files/s3objects.json > /dev/null; then
    echo "No bucket objects to search for creds"
else
    json_data=$(cat json-files/s3objects.json)
    keys=$(echo "$json_data" | jq -r '.[] | .Key')
    for key in $keys; do
    	bucket=$(echo "$json_data" | jq -r ".[] | select(.Key == \"$key\") | .Bucket")
		aws s3 cp s3://$bucket/$key json-files/objectdata.txt --profile cloudgoat2
		trufflehog filesystem --no-update json-files/objectdata.txt > json-files/gourouni.txt
		 if [ -s json-files/gourouni.txt ]; then
    		creds=$(grep "Raw result" json-files/gourouni.txt)
            if echo "$creds" | grep -q "BEGIN OPENSSH PRIVATE KEY"; then
                jq --arg key "$key" --arg creds "keypair" '(.[] | select(.Key == $key)) |= .+ {"HasCredsFor": $creds}' json-files/s3objects.json > temp && mv temp json-files/s3objects.json                
            else
        		creds=$(grep "Raw result" json-files/gourouni.txt  | head -n 1 | awk '{print $NF}')
                usercreds=$(aws iam get-access-key-last-used --access-key-id $creds --profile cloudgoat2 --query 'UserName' --output text)
        		jq --arg key "$key" --arg creds "$usercreds" '(.[] | select(.Key == $key)) |= .+ {"HasCredsFor": $creds}' json-files/s3objects.json > temp && mv temp json-files/s3objects.json
    	    fi
        fi
    done
fi
