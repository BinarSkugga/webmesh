import configparser
import subprocess
import sys
import importlib
from contextlib import contextmanager
from typing import List

from setuptools import setup


@contextmanager
def substituted_config():
    with open('setup.cfg', 'r') as cfg:
        template_cfg = cfg.read()

    try:
        from envsubst import envsubst
        substituted_config_text = envsubst(template_cfg)
        with open('setup.cfg', 'w') as cfg:
            cfg.write(substituted_config_text)

        yield template_cfg, substituted_config_text
    finally:
        with open('setup.cfg', 'w') as cfg:
            cfg.write(template_cfg)


def install(*packages: str):
    subprocess.run([sys.executable, '-m', 'pip', 'install', '-U', *packages])

    for p in packages:
        p = p.rstrip('=<>0123456789.~^*')
        globals()[p] = importlib.import_module(p)


if __name__ == '__main__':
    install('toml')
    import toml

    with open('pyproject.toml') as project_toml:
        toml_requirements = toml.load(project_toml)
    install(*toml_requirements['build-system']['requires'])

    with substituted_config() as (template, substituted):
        configs = configparser.ConfigParser()
        configs.read_string(substituted)
        requirements = configs['options']['install_requires'].split('\n')[1:]
        install(*requirements)

        setup()
