#!/bin/bash

pause(){
 read -n1 -rsp $'\n'
}

showhelp(){
  echo -e "\nHelp"
  echo "-e: name of environment: development, validation, preproduction, production (case sensitive)."
  echo "-p: Credentials profile to use."
  echo "-ad|--automatic-deployment: [Optional] app is being deployed by CI/CD process."
  echo -e "\n-h|--help: Display help."
  exit 1

}

while test $# -gt 0; do
  case "$1" in
    -h|--help)
      showhelp
      ;;
    -ad|--ad|--automatic-deployment)
      automatic="true"
      echo -e "\nusing options for automatic deployment."
      extraArgs="--ci --require-approval=never"
      echo "options: $extraArgs ."
      shift
      ;;
    -e|--e|--env|--environment)
      shift
      env=$1
      case $env in
        development)
            profile="deploy.dev.atlas";;
        validation)
            profile="deploy.valid.atlas";;
        preproduction)
            profile="deploy.preprod.atlas";;
        production)
            profile="deploy.prod.atlas";;
        *)
          echo "Please provide a valid environment name."
          showhelp
          exit 1;;
        esac
      shift
      ;;
    -p|--p|--profile)
      shift
      if test $# -gt 0; then
        profile="$1"
      fi
      shift
      ;;
    *)
    echo "Please provide a valid environment name."
    showhelp
    exit 1
    ;;

  esac
done


if [ -z "$env" ]; then
    echo "environment not provided."
    showhelp
    exit 1
fi

if [ -z "$VERSION" ]; then
  VERSION=$(git rev-parse --short HEAD)
fi

if [ -z "$BRANCH" ]; then
  BRANCH=$(git branch --show-current)
fi

echo "BRANCH = $BRANCH"
echo "VERSION = $VERSION"

export BRANCH=$BRANCH
export VERSION=$VERSION


echo -e "\nDeployment environment : $env"
echo "Use profile named: $profile"
echo "VERSION=$VERSION"
echo "branch=$BRANCH"




scriptsDirectory="scripts"
appDirName="aopcs_lambda/target/aws"
repoDirName="aopcs-lambda"
preRootDir=$(echo $(pwd) | awk -F /$repoDirName '{print $1}')

# ensure virtual environment is activated
if [[ "$VIRTUAL_ENV" == "" ]]
then
    echo "Activating virtual environment."
    cd $preRootDir
    source venv/bin/activate
fi;


cdkAppFullPath="$preRootDir/$repoDirName/$appDirName"
echo "cd $cdkAppFullPath"
cd $cdkAppFullPath


echo ""
echo "================================"
echo "##         Diff for CDK       ##"
echo "================================"
echo ""
cdk diff --all -c environment=$env --profile $profile
error_code=$?
if (( error_code > 0 )); then
    echo "Error during cdk diff process."
    exit $error_code
fi

if [ -z "$automatic" ]; then
    echo ""
    echo "================================"
    echo "## Press any key to deploy CDK ##"
    echo "================================"
    echo ""
    pause
fi

cdk deploy --app cdk.out --all --profile $profile -c environment=$env $extraArgs
error_code=$?
if (( error_code > 0 )); then
    echo "Error during cdk deploy process."
    exit $error_code
fi
