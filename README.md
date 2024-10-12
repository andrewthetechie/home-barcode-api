# barcode_api

This is an api that does stuff with barcodes. It is written for my personal home automation needs. It is shared on github just for visibility.

It is massively overengineered. I use it as a testbed and to learn new things.

## Developer Guide

### Poe

This Repo uses the [Poe task runner](https://github.com/nat-n/poethepoet?tab=readme-ov-file) to automate some tasks.

You can install Poe globally with pipx or install and run it with poetry as part of the repo's dev requirements

```shell

# installed globally
poe

# with poetry
poetry run poe
# or
poetry shell
poe
```

Runing poe without any arguments will list the available tasks. They are also in pyproject.toml
