#!/usr/bin/env bash

set -e

manifest_file="manifest.yaml"
image_without_tag="eu.gcr.io/cognitedata-development/pingpong-slackbot"
pattern=".*$image_without_tag:([0-9]+).*"
if [[ $(<$manifest_file) =~ $pattern ]] 
then
	tag="${BASH_REMATCH[1]}"
  new_tag=$(( tag + 1 ))
	old_image="$image_without_tag:$tag"
	new_image="$image_without_tag:$new_tag"
else
	echo "could find tag to replace in manifest"
	exit 1
fi

echo "old image: $old_image"
echo "new image: $new_image"

docker build . -t $new_image
CLOUDSDK_PYTHON=/usr/bin/python3 docker push $new_image

echo replacing image in manifest
sed -i "" "s+$old_image+$new_image+" $manifest_file

kubectl --context dev apply -f $manifest_file
