# Setup Router
### Get Opnsense Api Keys

You need the keys from Opnsense, to do that follow the instructions here in opnsenses (documentation)[https://docs.opnsense.org/development/how-tos/api.html#creating-keys]

**NOTE**: It downloads a file you need BOTH the `key` and `secret`

### Put in Infisical

You then need to put the `key` and `secret` into infisical, to do that follow this documentation for adding the keys to a new project (infisical documentation)[https://infisical.com/docs/documentation/platform/project]

Once you add the secrets to infisical then you need to get a client machine setup you can follow this documentation to get the client id and secret created (infisical documentation)[https://infisical.com/docs/documentation/platform/identities/universal-auth]

### Get Keys From Infisical Onto Machine

Clone this repo and then you need to edit `router/default.yaml` to have the infisical `client-id`. Then you need to run `export INFISICAL_CLIENT_SECRET=<infiscal-client-secret>`


### Running Setup

You then need to run `bootstrap-system.sh $HOME` as `sudo` which will install the various dependencies and the python venv where ansible is installed.

Once that finishes you need to run `source ~/ansible-venv/bin/activate` to enter the python venv and you can then push the changes to the router with `ansible-playbook -u user router/default.yaml`


### Done

Then Opnsense should be setup!

