#!/bin/bash

raw_version=`cat ../VERSION`
semver=( ${raw_version//./ } )
major="${semver[0]}"
minor="${semver[1]}"
patch="${semver[2]}"
echo "old version: $major.$minor.$patch"

if [ $1 == "major" ];
  then
    major=$((major + 1))
elif [ $1 == "minor" ];
  then
    minor=$((minor + 1))
elif [ $1 == "patch" ];
  then
    patch=$((patch + 1))
fi

CLEAN_VERSION="${major}_${minor}_${patch}"
echo "new version: $major.$minor.$patch"
if [ -f changelogs/$CLEAN_VERSION.md ]
  then
    echo -e "${RED}Fatal: File changelogs/$CLEAN_VERSION.md already exists${NC}"
    exit 1
  else
    git stash --quiet
    mv changelogs/current.md changelogs/$CLEAN_VERSION.md
    rm changelogs/latest.md
    ln -s changelogs/$CLEAN_VERSION.md changelogs/latest.md
    cp changelogs/.template.md changelogs/current.md
fi

echo "$major.$minor.$patch" > ../VERSION

git add changelogs/$CLEAN_VERSION.md
git commit -m "Bump version to $major.$minor.$patch" changelogs/current.md changelogs/$CLEAN_VERSION.md changelogs/latest.md ../VERSION
git stash apply --quiet