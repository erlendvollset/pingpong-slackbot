#!/usr/bin/env bash

set -e

manifest_file="manifest.yaml"
image_without_tag="eu.gcr.io/cognitedata-development/pingpong-slackbot"
pattern=".*$image_without_tag:([0-9]+).*"

if ! [[ $(<$manifest_file) =~ $pattern ]]
then
  echo "could find tag to replace in manifest"
  exit 1
fi

tag="${BASH_REMATCH[1]}"
new_tag=$(( tag + 1 ))
old_image="$image_without_tag:$tag"
new_image="$image_without_tag:$new_tag"

echo -e "\n*** Replacing image tag in manifest"
echo "old: $old_image"
echo "new: $new_image"
sed -i "" "s+$old_image+$new_image+" $manifest_file

echo -e "\n*** Building docker image"
docker build . -t $new_image

echo -e "\n*** Pushing docker image"
CLOUDSDK_PYTHON=/usr/bin/python3 docker push $new_image

echo -e "\n*** Applying manifest in cognitedata-development"
kubectl --context dev apply -f $manifest_file
