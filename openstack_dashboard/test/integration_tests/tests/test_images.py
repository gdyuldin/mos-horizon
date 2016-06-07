#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

from openstack_dashboard.test.integration_tests import decorators, helpers
from openstack_dashboard.test.integration_tests.regions import messages

IMAGE_NAME = helpers.gen_random_resource_name("image")


class TestImagesBasic(helpers.TestCase):

    @property
    def images_page(self):
        return self.home_pg.go_to_compute_imagespage()

    def image_create(self, image_name=IMAGE_NAME, local_file=None):
        images_page = self.images_page
        if local_file:
            images_page.create_image(image_name,
                                     image_source_type='file',
                                     image_file=local_file)
        else:
            images_page.create_image(image_name)
        self.assertTrue(images_page.find_message_and_dismiss(messages.SUCCESS))
        self.assertFalse(images_page.find_message_and_dismiss(messages.ERROR))
        self.assertTrue(images_page.is_image_present(image_name))
        self.assertTrue(images_page.is_image_active(image_name))
        return images_page

    def image_delete(self, image_name):
        images_page = self.images_page
        images_page.delete_image(image_name)
        self.assertTrue(images_page.find_message_and_dismiss(messages.SUCCESS))
        self.assertFalse(images_page.find_message_and_dismiss(messages.ERROR))
        self.assertFalse(images_page.is_image_present(image_name))

    def test_image_create_delete(self):
        """tests the image creation and deletion functionalities:
        * creates a new image from horizon.conf http_image
        * verifies the image appears in the images table as active
        * deletes the newly created image
        * verifies the image does not appear in the table after deletion
        """
        self.image_create()
        self.image_delete(IMAGE_NAME)

    def test_delete_images(self):
        names = [IMAGE_NAME + str(i) for i in range(3)]
        for name in names:
            images_page = self.image_create(name)

        name = names.pop()
        images_page.delete_images(name)
        self.assertTrue(images_page.find_message_and_dismiss(messages.SUCCESS))
        self.assertFalse(images_page.find_message_and_dismiss(messages.ERROR))
        self.assertFalse(images_page.is_image_present(name))

        images_page.delete_images(*names)
        self.assertTrue(images_page.find_message_and_dismiss(messages.SUCCESS))
        self.assertFalse(images_page.find_message_and_dismiss(messages.ERROR))
        self.assertSequenceFalse(
            [images_page.is_image_present(name) for name in names])

    def test_image_create_delete_from_local_file(self):
        """tests the image creation and deletion functionalities:
        * downloads image from horizon.conf stated in http_image
        * creates the image from the downloaded file
        * verifies the image appears in the images table as active
        * deletes the newly created image
        * verifies the image does not appear in the table after deletion
        """
        with helpers.gen_temporary_file() as file_name:
            self.image_create(local_file=file_name)
            self.image_delete(IMAGE_NAME)

    def test_images_pagination(self):
        """This test checks images pagination
            Steps:
            1) Login to Horizon Dashboard as horizon user
            2) Navigate to user settings page
            3) Change 'Items Per Page' value to 1
            4) Go to Project -> Compute -> Images page
            5) Check that only 'Next' link is available, only one image is
            available (and it has correct name)
            6) Click 'Next' and check that both 'Prev' and 'Next' links are
            available, only one image is available (and it has correct name)
            7) Click 'Next' and check that only 'Prev' link is available,
            only one image is visible (and it has correct name)
            8) Click 'Prev' and check results (should be the same as for step6)
            9) Click 'Prev' and check results (should be the same as for step5)
            10) Go to user settings page and restore 'Items Per Page'
        """
        first_image = "image_1"
        self.image_create(first_image)
        second_image = "image_2"
        self.image_create(second_image)
        third_image = self.CONFIG.image.images_list[0]
        items_per_page = 1

        first_page_definition = {'Next': True, 'Prev': False,
                                 'Count': items_per_page,
                                 'Names': [first_image]}
        second_page_definition = {'Next': True, 'Prev': True,
                                  'Count': items_per_page,
                                  'Names': [second_image]}
        third_page_definition = {'Next': False, 'Prev': True,
                                 'Count': items_per_page,
                                 'Names': [third_image]}

        settings_page = self.home_pg.go_to_settings_usersettingspage()
        settings_page.change_pagesize(items_per_page)
        settings_page.find_message_and_dismiss(messages.SUCCESS)

        images_page = self.images_page
        images_page.images_table.assert_definition(first_page_definition)

        images_page.images_table.turn_next_page()
        images_page.images_table.assert_definition(second_page_definition)

        images_page.images_table.turn_next_page()
        images_page.images_table.assert_definition(third_page_definition)

        images_page.images_table.turn_prev_page()
        images_page.images_table.assert_definition(second_page_definition)

        images_page.images_table.turn_prev_page()
        images_page.images_table.assert_definition(first_page_definition)

        settings_page = self.home_pg.go_to_settings_usersettingspage()
        settings_page.change_pagesize()
        settings_page.find_message_and_dismiss(messages.SUCCESS)

        self.image_delete(second_image)
        self.image_delete(first_image)

    def test_update_image_metadata(self):
        """Test update image metadata
        * logs in as admin user
        * creates image from locally downloaded file
        * verifies the image appears in the images table as active
        * invokes action 'Update Metadata' for the image
        * adds custom filed 'metadata'
        * adds value 'image' for the custom filed 'metadata'
        * gets the actual description of the image
        * verifies that custom filed is present in the image description
        * deletes the image
        * verifies the image does not appear in the table after deletion
        """
        new_metadata = {'metadata1': helpers.gen_random_resource_name("value"),
                        'metadata2': helpers.gen_random_resource_name("value")}

        with helpers.gen_temporary_file() as file_name:
            images_page = self.image_create(local_file=file_name)
            images_page.add_custom_metadata(IMAGE_NAME, new_metadata)
            results = images_page.check_image_details(IMAGE_NAME,
                                                      new_metadata)
            self.image_delete(IMAGE_NAME)
            self.assertSequenceTrue(results)

    def test_remove_protected_image(self):
        """tests that protected image is not deletable
        * logs in as admin user
        * creates image from locally downloaded file
        * verifies the image appears in the images table as active
        * marks 'Protected' checkbox
        * verifies that edit action was successful
        * verifies that delete action is not available in the list
        * tries to delete the image
        * verifies that exception is generated for the protected image
        * unmarks 'Protected' checkbox
        * deletes the image
        * verifies the image does not appear in the table after deletion
        """
        with helpers.gen_temporary_file() as file_name:
            images_page = self.image_create(local_file=file_name)
            images_page.edit_image(IMAGE_NAME, protected=True)
            self.assertTrue(
                images_page.find_message_and_dismiss(messages.SUCCESS))

            # Check that Delete action is not available in the action list.
            # The below action will generate exception since the bind fails.
            # But only ValueError with message below is expected here.
            with self.assertRaisesRegexp(ValueError, 'Could not bind method'):
                images_page.delete_image(IMAGE_NAME)

            # Try to delete image. That should not be possible now.
            images_page.delete_images(IMAGE_NAME)
            self.assertFalse(
                images_page.find_message_and_dismiss(messages.SUCCESS))
            self.assertTrue(
                images_page.find_message_and_dismiss(messages.ERROR))
            self.assertTrue(images_page.is_image_present(IMAGE_NAME))

            images_page.edit_image(IMAGE_NAME, protected=False)
            self.assertTrue(
                images_page.find_message_and_dismiss(messages.SUCCESS))
            self.image_delete(IMAGE_NAME)

    def test_edit_image_description_and_name(self):
        """tests that image description is editable
        * creates image from locally downloaded file
        * verifies the image appears in the images table as active
        * toggle edit action and adds some description
        * verifies that edit action was successful
        * verifies that new description is seen on image details page
        * toggle edit action and changes image name
        * verifies that edit action was successful
        * verifies that image with new name is seen on the page
        * deletes the image
        * verifies the image does not appear in the table after deletion
        """
        new_description_text = helpers.gen_random_resource_name("description")
        new_image_name = helpers.gen_random_resource_name("image")
        with helpers.gen_temporary_file() as file_name:
            images_page = self.image_create(local_file=file_name)
            images_page.edit_image(IMAGE_NAME,
                                   description=new_description_text)
            self.assertTrue(
                images_page.find_message_and_dismiss(messages.SUCCESS))
            self.assertFalse(
                images_page.find_message_and_dismiss(messages.ERROR))

            results = images_page.check_image_details(IMAGE_NAME,
                                                      {'Description':
                                                       new_description_text})
            self.assertSequenceTrue(results)

            # Just go back to the images page and toggle edit again
            images_page = self.images_page
            images_page.edit_image(IMAGE_NAME,
                                   new_name=new_image_name)
            self.assertTrue(
                images_page.find_message_and_dismiss(messages.SUCCESS))
            self.assertFalse(
                images_page.find_message_and_dismiss(messages.ERROR))

            results = images_page.check_image_details(new_image_name,
                                                      {'Name':
                                                       new_image_name})
            self.assertSequenceTrue(results)

            self.image_delete(new_image_name)


class TestImagesAdvanced(TestImagesBasic):
    """Login as demo user"""

    @property
    def images_page(self):
        return self.home_pg.go_to_compute_imagespage()

    def test_create_volume_from_image(self):
        """This test case checks create volume from image functionality:
            Steps:
            1. Login to Horizon Dashboard as regular user
            2. Navigate to Project -> Compute -> Images
            3. Create new volume from image
            4. Check that volume is created with expected name
            5. Check that volume status is Available
        """
        images_page = self.images_page
        source_image = self.CONFIG.image.images_list[0]
        target_volume = "created_from_{0}".format(source_image)

        volumes_page = images_page.create_volume_from_image(
            source_image, volume_name=target_volume)
        self.assertTrue(
            volumes_page.find_message_and_dismiss(messages.INFO))
        self.assertFalse(
            volumes_page.find_message_and_dismiss(messages.ERROR))
        self.assertTrue(volumes_page.is_volume_present(target_volume))
        self.assertTrue(volumes_page.is_volume_status(target_volume,
                                                      'Available'))
        volumes_page.delete_volume(target_volume)
        volumes_page.find_message_and_dismiss(messages.SUCCESS)
        volumes_page.find_message_and_dismiss(messages.ERROR)
        self.assertTrue(volumes_page.is_volume_deleted(target_volume))

    @decorators.skip_new_design
    def test_launch_instance_from_image(self):
        """This test case checks launch instance from image functionality:
            Steps:
            1. Login to Horizon Dashboard as regular user
            2. Navigate to Project -> Compute -> Images
            3. Launch new instance from image
            4. Check that instance is create
            5. Check that status of newly created instance is Active
            6. Check that image_name in correct in instances table
        """
        images_page = self.images_page
        source_image = self.CONFIG.image.images_list[0]
        target_instance = "created_from_{0}".format(source_image)
        instances_page = images_page.launch_instance_from_image(
            source_image, target_instance)
        self.assertTrue(
            instances_page.find_message_and_dismiss(messages.SUCCESS))
        self.assertFalse(
            instances_page.find_message_and_dismiss(messages.ERROR))
        self.assertTrue(instances_page.is_instance_active(target_instance))
        actual_image_name = instances_page.get_image_name(target_instance)
        self.assertEqual(source_image, actual_image_name)

        instances_page.delete_instance(target_instance)
        self.assertTrue(
            instances_page.find_message_and_dismiss(messages.SUCCESS))
        self.assertFalse(
            instances_page.find_message_and_dismiss(messages.ERROR))
        self.assertTrue(instances_page.is_instance_deleted(target_instance))

    @decorators.skip_new_design
    def test_edit_image_disk_and_ram_size(self):
        """tests that it is not possible to launch instances in case of limits
        * logs in as admin user
        * creates image from locally downloaded file
        * verifies the image appears in the images table as active
        * sets minimum disk value to 60
        * verifies that edit action was successful
        * executes launch image action
        * verifies that minimum possible flavor to launch is m1.large
        * sets minimum disk value to 0 and minimum ram value to 4096
        * verifies that edit action was successful
        * executes launch image action
        * verifies that minimum possible flavor to launch is m1.medium
        * deletes the image
        * verifies the image does not appear in the table after deletion
        """
        images_page = self.image_create()

        images_page.edit_image(IMAGE_NAME, minimum_disk=60)
        self.assertTrue(images_page.find_message_and_dismiss(messages.SUCCESS))
        self.assertFalse(images_page.find_message_and_dismiss(messages.ERROR))
        self.assertLaunchedFlavorIs('m1.large', images_page)

        images_page.edit_image(IMAGE_NAME, minimum_disk=0,
                               minimum_ram=4096)
        self.assertTrue(images_page.find_message_and_dismiss(messages.SUCCESS))
        self.assertFalse(images_page.find_message_and_dismiss(messages.ERROR))
        self.assertLaunchedFlavorIs('m1.medium', images_page)

        self.image_delete()

    def assertLaunchedFlavorIs(self, expected_flavor_name, images_page):
        launch_instance_form = images_page.get_launch_instance_form(
            IMAGE_NAME)
        flavor_name = launch_instance_form.flavor.text
        launch_instance_form.cancel()
        self.assertEqual(flavor_name, expected_flavor_name)

    def test_public_image_visibility(self):
        image_name = self.CONFIG.image.images_list[0]
        self.assertTrue(self.images_page.is_image_present(image_name))


class TestImagesAdmin(helpers.AdminTestCase, TestImagesBasic):
    """Login as admin user"""
    IMAGE_NAME = helpers.gen_random_resource_name("image")

    @property
    def images_page(self):
        return self.home_pg.go_to_system_imagespage()
