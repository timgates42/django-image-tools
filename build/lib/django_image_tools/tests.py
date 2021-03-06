# Created by Bonsai Studio <info@bonsai-studio.net>
# Copyright (C) Bonsai Studio
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

from __future__ import absolute_import
from django.core.files import File

from django.test import TestCase
from .models import *


def create_dummy_image(filename=u'Test_image', title=u'Title', caption=u'Caption', alt_text=u'Alt Text',
                       credit=u'Credit'):
    im = PILImage.new('RGB', (100, 50))
    im.save(u'{0}/{1}/test_input.jpg'.format(settings.MEDIA_ROOT, settings.DJANGO_IMAGE_TOOLS_CACHE_DIR))
    image = Image(filename=filename, title=title, caption=caption, alt_text=alt_text, credit=credit)
    with open(u'{0}/{1}/test_input.jpg'.format(settings.MEDIA_ROOT, settings.DJANGO_IMAGE_TOOLS_CACHE_DIR), 'r') as f:
        image.image.save(u'testjpg.jpg', File(f))
    return image


def delete_image(image_object):
    if os.path.exists(path_for_image(image_object)):
        os.remove(path_for_image(image_object))
    image_object.delete()


class SimpleTest(TestCase):

    def setUp(self):
        """
        Add a new image
        """

        create_dummy_image('testjpg', 'Test', 'Test', 'Test', 'None')

        im = PILImage.new('RGB', (150, 100))
        im.save(u'{0}/{1}/test_input_bmp.bmp'.format(settings.MEDIA_ROOT, settings.DJANGO_IMAGE_TOOLS_CACHE_DIR))
        imagew = Image(filename=u'wasbmp', title=u'Test', caption=u'Test', alt_text=u'Test', credit=u'none.')
        with open(u'{0}/{1}/test_input_bmp.bmp'.format(settings.MEDIA_ROOT, settings.DJANGO_IMAGE_TOOLS_CACHE_DIR), 'r') as f:
            imagew.image.save(u'{0}/{1}/testbmp.bmp'.format(settings.MEDIA_ROOT, settings.DJANGO_IMAGE_TOOLS_CACHE_DIR), File(f))

        size = Size(name=u'thumbnail', width=30, height=30)
        size.save()
        self.size = size

        long = Size(name=u'very_long', width=200, height=30)
        long.save()
        self.long = long

        tall = Size(name=u'very_tall', width=30, height=200)
        tall.save()
        self.tall = tall

        huge = Size(name=u'huge', width=2000, height=2000)
        huge.save()
        self.huge = huge

        bw = Filter(name=u'grey_scaled', filter_type=0)
        bw.save()

        self.imagepath = u'{0}/test_image.jpg'.format(settings.MEDIA_ROOT)
        self.imagewpath = u'{0}/wasbmp.jpg'.format(settings.MEDIA_ROOT)

    def testCreation(self):
        """
        Test that the saving happened
        """
        image = Image.objects.get(filename=u'test_image')
        self.assertTrue(os.path.exists(path_for_image(image)))
        self.assertEqual(Image.objects.all().count(), 2) # There should be two images in the db
        self.assertEqual(Image.objects.all()[0].filename, u'test_image')
        self.assertEqual(path_for_image(image), self.imagepath)

    def testJPGConversion(self):
        """
        Test that the new image has the right name and is in the right directory
        """
        image = Image.objects.get(filename=u'test_image')
        imagew = Image.objects.get(filename=u'wasbmp')

        self.assertEqual(path_for_image(image), self.imagepath)

        self.assertEqual(path_for_image(imagew), self.imagewpath)
        img = PILImage.open(path_for_image(imagew))
        self.assertEqual(img.format, u'JPEG')


    def testApplyFilter(self):
        """
        Test that applying a filter results in a new image created correctly.
        """
        image = Image.objects.get(filename=u'test_image')
        bw = Filter.objects.get(name=u'grey_scaled')

        if os.path.exists(path_for_image_with_filter_and_size(image, bw, self.size)):
            os.remove(path_for_image_with_filter_and_size(image, bw, self.size))
        self.assertFalse(os.path.exists(path_for_image_with_filter_and_size(image, bw, self.size)))
        self.assertEqual(image.get__grey_scaled__thumbnail,
                         media_path_for_image_with_filter_and_size(image, bw, self.size))
        self.assertTrue(os.path.exists(path_for_image_with_filter_and_size(image, bw, self.size)))


    def testOriginalFilter(self):
        """
        Test that applying a filter results in a new image created correctly.
        """
        image = Image.objects.get(filename=u'test_image')
        bw = Filter.objects.get(name=u'grey_scaled')

        if os.path.exists(path_for_image_with_filter_and_size(image, bw, None)):
            os.remove(path_for_image_with_filter_and_size(image, bw, None))
        self.assertFalse(os.path.exists(path_for_image_with_filter_and_size(image, bw, None)))
        self.assertEqual(image.get__grey_scaled__original,
                         media_path_for_image_with_filter_and_size(image, bw, None))
        self.assertTrue(os.path.exists(path_for_image_with_filter_and_size(image, bw, None)))

    def testRenaming(self):
        """
        Test that an image can be renamed correctly
        """
        image = Image.objects.get(filename=u'test_image')

        image.filename = u'renamed'
        image.save()
        self.assertTrue(os.path.exists(path_for_image(image)))
        self.assertFalse(os.path.exists(self.imagepath))
        image = Image.objects.get(filename=u'renamed')
        image.filename = u'test_image'
        image.save()

    def testResize(self):
        """
        Now add a simple size, and test that the resizing system works
        """
        image = Image.objects.get(filename=u'test_image')

        self.assertEqual(image.get__thumbnail, u'/media/cache/test_image_thumbnail.jpg')
        self.assertTrue(os.path.exists(path_for_image_with_size(image, self.size)))

    def testLazyCreation(self):
        """
        Test that the new image is created on request
        """
        self.size.width = 250
        self.size.height = 250
        self.size.save()
        image = Image.objects.all()[0]
        self.assertEqual(image.get__thumbnail, u'/media/cache/test_image_thumbnail.jpg')
        self.assertTrue(os.path.exists(path_for_image_with_size(image, self.size)))

        img = PILImage.open(path_for_image_with_size(image, self.size))
        self.assertTrue(img.size[0] == 250 and img.size[1] == 250)

    def test_rename_exception(self):
        """
        Test that renaming another image with the same name of an existing one will trigger an exception
        """
        image = Image.objects.get(filename=u'test_image')
        image2 = Image.objects.get(filename=u'wasbmp')
        image2.filename = image.filename
        self.assertRaises(ValidationError, image2.save)

    def test_unicode(self):
        self.assertEqual(self.size.__unicode__(), u'thumbnail - (30, 30)')

    def test_reserved_keywords_in_size(self):
        error_causing = Size(name=u'huge__with_double_underscore', width=2000, height=2000)
        self.assertRaises(ValidationError, error_causing.save)

    def test_reserved_keywords_in_filters(self):
        error_causing = Filter(name=u'huge__with_double_underscore')
        self.assertRaises(ValidationError, error_causing.save)

    def test_thumbnail(self):
        image = Image.objects.get(filename=u'test_image')
        # When there IS a thumbnail, the code should be this
        self.assertEqual(image.thumbnail(), u'<img src="/media/cache/test_image_thumbnail.jpg" width="100" height="100" />')
        self.size.delete()
        image = Image.objects.get(filename=u'test_image')
        self.assertEqual(image.thumbnail(), u'<img src="/media/test_image.jpg" width="100" height="100" />')

    def test_title(self):
        image = Image.objects.get(filename=u'test_image')
        self.assertEqual(image.__unicode__(), u'Test')

    def test_weird_sizes(self):
        image = Image.objects.get(filename=u'test_image')
        self.assertEqual(image.get__very_long, media_path_for_image_with_size(image, self.long))
        img = PILImage.open(path_for_image_with_size(image, self.long))
        self.assertTrue(img.size[0] == self.long.width and img.size[1] == self.long.height)

        self.assertEqual(image.get__very_tall, media_path_for_image_with_size(image, self.tall))
        img = PILImage.open(path_for_image_with_size(image, self.tall))
        self.assertTrue(img.size[0] == self.tall.width and img.size[1] == self.tall.height)

    def test_upscale_check(self):
        """
        Test that when an image is upscaled, the info is saved onto the db
        """
        image = Image.objects.get(filename=u'test_image')
        self.assertFalse(image.was_upscaled)
        self.assertEqual(image.get__huge, media_path_for_image_with_size(image, self.huge))
        # Now the image was upscaled, so the flag should be true
        image = Image.objects.get(filename=u'test_image')
        self.assertTrue(image.was_upscaled)

    def tearDown(self):
        """
        Cleaning up what was created...
        """
        image = Image.objects.get(filename=u'test_image')
        imagew = Image.objects.get(filename=u'wasbmp')
        image.delete()
        imagew.delete()
        if os.path.exists(u'{0}/{1}/test_input.jpg'.format(settings.MEDIA_ROOT, settings.DJANGO_IMAGE_TOOLS_CACHE_DIR)):
            os.remove(u'{0}/{1}/test_input.jpg'.format(settings.MEDIA_ROOT, settings.DJANGO_IMAGE_TOOLS_CACHE_DIR))
        if os.path.exists(u'{0}/{1}/test_input_bmp.bmp'.format(settings.MEDIA_ROOT, settings.DJANGO_IMAGE_TOOLS_CACHE_DIR)):
            os.remove(u'{0}/{1}/test_input_bmp.bmp'.format(settings.MEDIA_ROOT, settings.DJANGO_IMAGE_TOOLS_CACHE_DIR))
        if self.size.pk is not None:
            self.size.delete()
        os.remove(path_for_image(image))
        os.remove(path_for_image(imagew))
