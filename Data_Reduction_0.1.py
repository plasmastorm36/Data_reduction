import PySimpleGUI as sg
from astropy.nddata import CCDData
from astropy.io import fits
import ccdproc
import glob


class Reduce:
    """
    Generates reduced image and master files
    """

    def bias(self):
        """
        gets the list of bias files from specified name, combines them into m_bias
        takes the median pixel values of all images and places them in one file
        :return:
        """
        bias_files = glob.glob(self + '*.fits')
        return ccdproc.combine(bias_files, method='median', unit='adu')

    def dark(self, m_bias):
        """
        makes a master dark file
        reads files from window, and removes bias, then finds divides each image by exposure time
        program then returns the median value of each pixel for the resulting image
        :param m_bias:
        :return:
        """
        dark_files = glob.glob(self + '*.fits')
        read = fits.open(dark_files[0])
        time = read[0].header['exptime']
        dark_read = []
        dark = []
        for i in range(len(dark_files)):
            dark_read.append(CCDData.read(dark_files[i], unit='adu'))
        for i in range(len(dark_files)):
            dark.append(CCDData.divide(CCDData.subtract(dark_read[i], m_bias), time))
        return ccdproc.combine(dark, method='median')

    def flat(self, bias, dark):
        """
        Returns master flat
        takes master bias and dark and uses them to correct the flat images
        the flat images have their median image found where then each flat image is divided by the median image
        their median pixel value is returned
        :param bias:
        :param dark:
        :return:
        """
        flat_files = glob.glob(self + '*.fits')
        flat = []
        flat_read = []
        flat_med = []
        for i in flat_files:
            flat_read.append(CCDData.read(i, unit='adu'))
        for i in range(len(flat_read)):
            flat_med.append(CCDData.subtract(flat_read[i], CCDData.subtract(bias, dark)))

        mid_flat = ccdproc.combine(flat_med, method='median')
        for i in range(len(flat_read)):
            flat.append(CCDData.divide(flat_read[i], mid_flat))
        return ccdproc.combine(flat, method='median', unit='adu')

    def sci(self, bias, dark, flat, name):
        image_list = glob.glob(self)
        image = CCDData.read(image_list[0], unit='adu')
        sci = CCDData.divide(CCDData.subtract(image, CCDData.subtract(dark, bias)), flat)
        image_file = fits.PrimaryHDU(sci)
        image_file.writeto(name, overwrite=True)


sg.theme('Dark Grey 13')

layout = [[sg.Text('Bias Filename')],
          [sg.Input(), sg.FileBrowse()],
          [sg.Text('Dark Filename')],
          [sg.Input(), sg.FileBrowse()],
          [sg.Text('Flat Filename')],
          [sg.Input(), sg.FileBrowse()],
          [sg.Text('Science Filename')],
          [sg.Input(), sg.FileBrowse()],
          [sg.Text('Name of reduced file')],
          [sg.Input(), sg.FileBrowse()],
          [sg.OK(), sg.Cancel()]]

window = sg.Window('Get filename example', layout)

text = window.read()

m_bias = Reduce.bias(text[1][0])
m_dark = Reduce.dark(text[1][1], m_bias)
m_flat = Reduce.flat(text[1][2], m_bias, m_dark)
Reduce.sci(text[1][3], m_bias, m_dark, m_flat, text[1][4])
window.close()
sg.popup("Done")
