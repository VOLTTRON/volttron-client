# -*- coding: utf-8 -*- {{{
# vim: set fenc=utf-8 ft=python sw=4 ts=4 sts=4 et:
#
# Copyright 2020, Battelle Memorial Institute.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# This material was prepared as an account of work sponsored by an agency of
# the United States Government. Neither the United States Government nor the
# United States Department of Energy, nor Battelle, nor any of their
# employees, nor any jurisdiction or organization that has cooperated in the
# development of these materials, makes any warranty, express or
# implied, or assumes any legal liability or responsibility for the accuracy,
# completeness, or usefulness or any information, apparatus, product,
# software, or process disclosed, or represents that its use would not infringe
# privately owned rights. Reference herein to any specific commercial product,
# process, or service by trade name, trademark, manufacturer, or otherwise
# does not necessarily constitute or imply its endorsement, recommendation, or
# favoring by the United States Government or any agency thereof, or
# Battelle Memorial Institute. The views and opinions of authors expressed
# herein do not necessarily state or reflect those of the
# United States Government or any agency thereof.
#
# PACIFIC NORTHWEST NATIONAL LABORATORY operated by
# BATTELLE for the UNITED STATES DEPARTMENT OF ENERGY
# under Contract DE-AC05-76RL01830
# }}}


""" Core package."""
from gevent import monkey

# At this point these are the only things that need to be patched
# and the server and client are working harmoniously with this.
patches = [
    ('ssl', monkey.patch_ssl),
    ('socket', monkey.patch_socket),
    ('os', monkey.patch_os),
]

# patch modules if necessary.  Only if the module hasn't been patched before.
# this could happen if the server code uses the client (which it does).
for module, fn in patches:
    if not monkey.is_module_patched(module):
        fn()

import logging
from pathlib import Path
import yaml
import os
import traceback

import psutil
import sys
from configparser import ConfigParser
from urllib.parse import urlparse

from pbr.version import VersionInfo

from volttron.utils import jsonapi
from volttron.utils.frozendict import FrozenDict


__version__ = VersionInfo("volttron.client")

_log = logging.getLogger(__name__)


# def get_volttron_root():
#     """
#     Returns the root folder where the volttron code base resideds on disk.

#     :return: absolute path to root folder
#     """
#     return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# def get_volttron_data():
#     root = get_volttron_root()
#     return os.path.join(root, "volttron_data")


# def get_services_core(agent_dir=None):
#     root = get_volttron_root()
#     services_core = os.path.join(root, "services/core")
#     if not agent_dir:
#         return services_core
#     return os.path.join(services_core, agent_dir)


# def get_ops(agent_dir=None):
#     root = get_volttron_root()
#     ops_dir = os.path.join(root, "services/ops")
#     if not agent_dir:
#         return ops_dir
#     return os.path.join(ops_dir, agent_dir)


# def get_examples(agent_dir):
#     root = get_volttron_root()
#     examples_dir = os.path.join(root, "examples")
#     if not agent_dir:
#         return examples_dir
#     return os.path.join(examples_dir, agent_dir)


# def is_instance_running(volttron_home=None):

#     if volttron_home is None:
#         volttron_home = get_home()

#     instance_file = os.path.expanduser("~/.volttron_instances")
#     if not os.path.isfile(instance_file):
#         return False

#     with open(instance_file, "r") as fp:
#         jsonobj = jsonapi.loads(fp.read())

#     if volttron_home not in jsonobj:
#         return False

#     obj = jsonobj[volttron_home]
#     pid = obj.get("pid", None)

#     if not pid:
#         return False

#     return psutil.pid_exists(pid)


# def is_rabbitmq_available():
#     rabbitmq_available = True
#     try:
#         import pika

#         rabbitmq_available = True
#     except ImportError:
#         os.environ["RABBITMQ_NOT_AVAILABLE"] = "True"
#         rabbitmq_available = False
#     return rabbitmq_available


# __config__ = None


# def get_platform_config():
#     global __config__
#     if os.environ.get("VOLTTRON_HOME") is None:
#         raise Exception("VOLTTRON_HOME must be specified before calling this function.")

#     if __config__ is None:
#         __config__ = FrozenDict()
#         volttron_home = get_home()
#         config_file = os.path.join(volttron_home, "config")
#         if os.path.exists(config_file):
#             parser = ConfigParser()
#             parser.read(config_file)
#             options = parser.options("volttron")
#             for option in options:
#                 __config__[option] = parser.get("volttron", option)
#             __config__.freeze()
#     return __config__


# def update_platform_config(values: dict) -> None:
#     global __config__

#     if __config__ is None:
#         cfg = get_platform_config()
#     else:
#         cfg = __config__
#         # Make sure we can update items
#         cfg._frozen = False

#     cfg.update(values)

#     config_file = get_config_path()
#     with open(config_file, "w") as fp:
#         p = ConfigParser()
#         p.add_section("volttron")
#         for k, v in cfg.items():
#             p.set("volttron", k, v)

#         cfg.freeze()
#         p.write(fp)

#     return get_platform_config()


def build_vip_address_string(vip_root, serverkey, publickey, secretkey):
    """Build a full vip address string based upon the passed arguments

    All arguments are required to be non-None in order for the string to be
    created successfully.

    :raises ValueError if one of the parameters is None.
    """
    _log.debug(
        "root: {}, serverkey: {}, publickey: {}, secretkey: {}".format(
            vip_root, serverkey, publickey, secretkey
        )
    )
    parsed = urlparse(vip_root)
    if parsed.scheme == "tcp":
        if not (serverkey and publickey and secretkey and vip_root):
            raise ValueError("All parameters must be entered.")

        root = "{}?serverkey={}&publickey={}&secretkey={}".format(
            vip_root, serverkey, publickey, secretkey
        )

    elif parsed.scheme == "ipc":
        root = vip_root
    else:
        raise ValueError("Invalid vip root specified!")

    return root


# def update_volttron_script_path(path: str) -> str:
#     """
#     Assumes that path's current working directory is in the root directory of the volttron codebase.

#     Prepend 'VOLTTRON_ROOT' to internal volttron script if 'VOLTTRON_ROOT' is set and return new path;
#     otherwise, return original path
#     :param path: relative path to the internal volttron script
#     :return: updated path to volttron script
#     """
#     if os.environ["VOLTTRON_ROOT"]:
#         args = path.split("/")
#         path = f"{os.path.join(os.environ['VOLTTRON_ROOT'], *args)}"
#     _log.debug(f"Path to script: {path}")
#     return path