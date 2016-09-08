"""
Network tests.

@author: schipiga@mirantis.com
"""

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import pytest

from .fixtures._utils import generate_ids


@pytest.mark.usefixtures('any_one')
class TestAnyOne(object):
    """Tests for any user."""

    def test_subnet_add(self, network, networks_steps):
        """Verify that user can add subnet."""
        subnet_name = next(generate_ids('subnet'))
        networks_steps.add_subnet(network.name, subnet_name)


@pytest.mark.usefixtures('admin_only')
class TestAdminOnly(object):
    """Tests for admin only."""

    def test_create_shared_network(self, horizon, networks_steps):
        """Verify that admin can create shared network."""
        network_name = next(generate_ids('network'))
        networks_steps.create_network(network_name, shared=True)

        networks_steps.delete_networks([network_name], check=False)
        networks_steps.close_notification('error')

        horizon.page_networks.table_networks.row(
            name=network_name).wait_for_presence()
        networks_steps.admin_delete_network(network_name)

    def test_create_delete_subnet(self, networks_steps, network):
        """Checks create delete subnet functionality"""
        subnet_name = next(generate_ids('subnet'))
        networks_steps.admin_add_subnet(network.name, subnet_name)

        networks_steps.admin_add_subnet(network.name, subnet_name, check=False)
        networks_steps.close_notification('error')

        networks_steps.admin_delete_subnet(network.name, subnet_name)

    def test_create_edit_delete_port(self, networks_steps, network):
        """Checks create/edit/delete port functionality"""
        port_name = next(generate_ids('port'))
        networks_steps.admin_add_port(network.name, port_name)

        new_port_name = next(generate_ids('new_port'))
        networks_steps.admin_update_port(network.name, port_name,
                                         new_port_name=new_port_name)

        networks_steps.admin_delete_port(network.name, new_port_name)


@pytest.mark.usefixtures('user_only')
class TestUserOnly(object):
    """Tests for demo only."""

    def test_not_create_shared_network(self, horizon, create_network):
        """Verify that demo can not create shared network."""
        network_name = next(generate_ids('network'))
        create_network(network_name, shared=True)

        assert horizon.page_networks.table_networks.row(
            name=network_name).cell('shared').value == 'No'