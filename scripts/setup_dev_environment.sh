#!/bin/bash
PYTHON_VERSION="3.12"
echo "This project uses python $PYTHON_VERSION. Make sure to have the correct version of Python on your environment."
echo "======================== DEACTIVATE ENVIRONMENT ========================"
echo ""
if [ -z "$VIRTUAL_ENV" ];
then
    echo "Virtual environment is already deactivated"
else
    deactivate
    echo "Virtual environment deactivated"
fi

echo ""
echo "======================= REMOVING OLD ENVIRONMENT ======================="
echo ""
echo "rm -rf venv"
rm -rf venv
echo "rm -rf env"
rm -rf env

echo ""
echo "======================= CREATING NEW ENVIRONMENT ======================="
echo ""
echo "python$PYTHON_VERSION -m venv venv"
python$PYTHON_VERSION -m venv venv

echo ""
echo "========================= ACTIVATE ENVIRONMENT ========================="
echo ""
echo "source venv/bin/activate"
source venv/bin/activate

echo ""
echo "================================ UPGRADE PIP ============================"
echo ""
echo "python -m pip install -U pip>=21.1"
python -m pip install -U 'pip>=21.1'

echo ""
echo "=========================== INSTALL DEPENDENCIES =========================="
echo ""
echo "pip install -r requirements.txt"
pip install -r requirements.txt

echo ""
echo "=========================== INSTALL DEV TOOLS =========================="
echo ""
echo "pip install -r requirements-dev.txt"
pip install -r requirements-dev.txt

echo ""
echo "=========================== INSTALL AWS REQUIREMENTS =========================="
echo ""

echo "pip3 install -r aopcs_lambda/target/aws/requirements.txt"
pip3 install -r aopcs_lambda/target/aws/requirements.txt


echo ""
echo "=========================== INSTALL TEST REQUIREMENTS =========================="
echo ""

echo "pip3 install -r tests/requirements.txt"
pip3 install -r tests/requirements.txt

echo ""
echo "=========================== INSTALL PROJECT ==========================="
echo ""
echo "pip3 install -e ."
pip3 install -e .

echo ""
echo "========================= INSTALLING PRE-COMMIT ========================"
echo ""
echo "pre-commit install"
pre-commit install
