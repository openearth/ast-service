# AST backend

This is the Python backend for the AST project, see the [WIKI](https://publicwiki.deltares.nl/display/AST/Climate+Resilient+City+Tool+and+KBS+Toolbox+Home) for more information. You should contact Reinder Brolsma or Daan Rooze with any questions.

This is a simple REST API that uses Flask to serve some basic computations endpoint for the websites https://crctool.org/ (English) and https://kbstoolbox.nl/nl/ (Dutch).
When rolled out, it should be live at https://ast-backend.deltares.nl.

## Installation
Ideally you use something like `micromamba` to create a new environment and install the dependencies from the `ast_environment.yml` file with `micromamba create -n ast --file ast_environment.yml`.

## Setting
Rename the config.txt.example to config.txt and fill it in before running.

## Running
When installed and in the right environment (`micromamba activate ast`), you should be able to run `python app.py` and have a live server to test with.

## Deployment
We use [Ansible](https://docs.ansible.com/ansible/latest/) to deploy this code to a server (currently c-oet08041.directory.intra).
You can install ansible with `pip install ansible` and then from the `ansible` directory run `ansible-playbook -i production site.yml -u <<USER>> -bk` to deploy the code. Please replace `<<USER>>` with your username.
