# https://stackoverflow.com/questions/41721734/take-screenshot-of-full-page-with-selenium-python-with-chromedriver
# https://stackoverflow.com/questions/31163450/converting-long-image-to-paged-pdf
# https://stackoverflow.com/questions/15018372/how-to-take-partial-screenshot-with-selenium-webdriver-in-python

from selenium import webdriver
from selenium.webdriver import FirefoxOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions

from PIL import Image
import os
import numpy as np
import json
import time
import json
import logging
import tempfile

logging.basicConfig(level=logging.DEBUG, 
                    format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                    filename='log',
                    filemode='w')

# Generate URL for a particular LDAP ID
def get_url(ldap):
    assert (isinstance(ldap, str) or isinstance(ldap, int))
    """
     We use a localhost server for the website
     It is necessary to specify the http protocol, so that selenium understands
     how to navigate it. If you directly use a file, the url should be like:
     file:///<path_to_html>
    """
    return "http://192.168.1.7:8000/student-%s" % ldap


class yb_processor:
    def __init__(self):
        # Set up Firefox profile
        self.firefox_profile = webdriver.FirefoxProfile()
        self.firefox_profile.set_preference("browser.privatebrowsing.autostart", True)

        # Configure options for Firefox webdriver
        self.options = FirefoxOptions()
        self.options.add_argument('--headless')
        self.options.add_argument("--hide-scrollbars")
        
        # Initialise Firefox webdriver
        self.driver = webdriver.Firefox(firefox_profile=self.firefox_profile,
                                        options=self.options)
        self.driver.maximize_window()
    
    def execute_script_wrapper(self, script):
        wrapped_script = f"$(document).ready(function(){{ {script}; }})"
        self.driver.execute_script(wrapped_script)
    
    def access_url(self, ldap):
        self.current_ldap = str(ldap)
        self.current_url = get_url(self.current_ldap)
        self.driver.get(self.current_url)
        self.fetched_url = True
    
    def clean_html(self, for_print=True):
        assert self.fetched_url
        
        jquery_scripts = [
            # Change background
            "$('body').css('background-image', 'url(../static/img/memphis.png)')",
            # Remove the nav bar
            "$('nav').remove()",
            # Correct the offset styles in <body> and its chidlren
            "$('.offset-top').removeClass('offset-top')",
            "$('body').css('padding-top', '7em')",
            #"$('body').css('padding-bottom', '7em')",
            # Remove the right arrow in front of the name
            "$('span.fa-caret-right').remove()",
            # Remove the "What they said" and "Like, Share, ..." lines
            "$('.list-inline, .post-buttons-list').remove()",
            # Remove the person's repeated name
            "$('div.user-details:odd').remove()",
            # Remove the "Write for ..." and "Show Image" buttons
            "$('button:lt(5)').remove()",
            # Remove the questions section if it is empty
            "if($('#answer-1').text() == 'No answer yet.') $('#answer-1').parents().eq(2).remove()",
            # Remove the "Share on FB" section
            "$('#myshare-text').remove()",
            "$('.fb-page').parent().remove()",
            # Adjust image tile padding
            "$('.image-container').css('padding-top', '15px')",
            # Allow names to extend without limit instead of wrapping around
            "$('.with-arrow').css('max-width', 'none').addClass('col-xs')",
            # Change the font css of the writer name
            "$('.with-arrow').children('a').css('font-size', 'x-large')",
            # Remove the writing ("post") container square design
            "$('.sub-post').css('background-color', 'transparent')",
            "$('.sub-post').css('box-shadow', '0 0 0 0')",
        ]
        
        for script in jquery_scripts:
            self.execute_script_wrapper(script)
        
    def add_pagebreak(self):
        ul, lr = self.get_cropping_dimensions()
        page_width = lr[0] - ul[0]
        print_style_offset_script = f"""
            // Maintain an aspect ratio of sqrt(2):1 like A4
            // a4_page_width = element.offset().left + element.width();
            a4_page_width = {page_width};  // output image width from screenshot()
            a4_page_height = Math.sqrt(2) * a4_page_width;
            
            // Initialise value of borders and margins
            page_border = a4_page_height;
            page_margin = $('.container-fluid').offset().top;
            
            $('.sub-post').each(function(index, element) {{
                // If the post's dimensions fall at the edge of the border, push it
                // to the next page with appropriate padding (current page difference + header margin)
                if($(element).offset().top + $(element).height() > page_border - page_margin){{
                    new_margin = parseInt($(element).css('margin-top')) + page_border + page_margin - $(element).offset().top;
                    $(element).delay(index*10).css('margin-top', new_margin);
                    page_border = a4_page_height + page_border;
                }}
            }})
            
            // Finally pad the last page so that it is a complete page
            padding_bottom = page_border - ($('.row').first().offset().top + $('.row').first().height()) - 1;
            $('body').css('padding-bottom', padding_bottom);
        """
        self.execute_script_wrapper(print_style_offset_script)
    
    def _stitch_screenshots_by_scrolling(self, img_name):
        original_size = self.driver.get_window_size()
        viewport_height = self.driver.execute_script("return window.innerHeight;")
        total_height = self.driver.execute_script("return document.body.scrollHeight;")

        stitched_image = Image.new('RGB', (original_size["width"], total_height))
        index, current_cumulative_height = 0, 0

        with tempfile.TemporaryDirectory() as tmpdirname:
            self.driver.execute_script("window.scrollTo(0, 0);")
            while True:
                # Take screenshot of current viewport
                screenshot_patch_file_name = f"{tmpdirname}/part_{index}.png"
                self.driver.get_screenshot_as_file(screenshot_patch_file_name)

                # Append screenshot of current window to original image file
                screenshot_patch = Image.open(screenshot_patch_file_name)
                # When on the last page, scroll position might actually differ from
                # current_cumulative_height because less than viewport_height scroll
                # area is left
                current_scroll_position = self.driver.execute_script("""
                    return document.documentElement.scrollTop || document.body.scrollTop;""")
                stitched_image.paste(screenshot_patch, (0, current_scroll_position))
                
                del screenshot_patch
                os.remove(screenshot_patch_file_name)

                # Prepare for scrolling
                index += 1
                current_cumulative_height += viewport_height
                if current_cumulative_height > total_height:
                    break
                self.driver.execute_script(f"window.scrollBy(0, {viewport_height});")

            stitched_image.save(img_name)

    def get_screenshot(self, img_name=None):
        assert self.fetched_url
        if img_name is None:
            img_name = f"{self.current_ldap}.png"
        
        #ss_xpath = '//div[@class="container-fluid offset-top"]//div[@class="row"]'
        ss_xpath = '//body'
        # body_element = self.driver.find_element_by_xpath(ss_xpath)
        # successful = body_element.screenshot(img_name)
        # if successful:
        #     return img_name

        self._stitch_screenshots_by_scrolling(img_name)
        return img_name
        
    # Crop a given image using upper left and lower right coordinates
    def crop_image(self, img_path = None):
        ul, lr = self.get_cropping_dimensions()
        if img_path == None:
            img_path = f"{self.current_ldap}.png"
        img = Image.open(img_path)
        ul, lr = self.get_cropping_dimensions()
        page_width = lr[0] - ul[0]

        img = img.crop((*ul, *lr))
        img.save(img_path)
    
    # Get cropping dimensions for a screenshot
    def get_cropping_dimensions(self):
        assert self.fetched_url
        element = self.driver.find_element_by_xpath(
            '//div[@class="col-sm-12 col-md-8 col-md-offset-2 col-lg-8 col-lg-offset-2"]')
        size = element.size
        location = element.location
        
        body_element = self.driver.find_element_by_xpath('//body')
        body_size = body_element.size
        body_location = body_element.location
        
        original_size = self.driver.get_window_size()
        
        x1, y1 = location['x'], body_location['y']
        x2, y2 = x1 + size['width'], y1 + body_size['height']
        
        return (x1-x1/2, y1), (x2+x1/2, y2)
    
    def create_pdf(self,img_name=None,pdf_name=None, remove=True):
        if pdf_name is None:
            pdf_name = f"{self.current_ldap}.pdf"
        if img_name is None:
            img_name = f"{self.current_ldap}.png"
        ul, lr = self.get_cropping_dimensions()
        X = np.ceil(lr[0] - ul[0])
        Y = X * np.sqrt(2)
        os.system(f'convert -density 300 {img_name} -crop {X}x{Y} +repage {pdf_name}')
        if remove:
            os.system(f'rm -f {img_name}')
        if not os.path.exists(f"{pdf_name}"):
            #self.cleanup()
            raise ValueError
    
    def create_archive(self):
        os.system(f'zip -q {self.current_ldap}.zip yearbook.png yearbook.pdf')
        #os.system(f'zip -q {self.current_ldap}.zip {self.current_ldap}.png {self.current_ldap}.pdf')

    def cleanup(self):
        os.system(f'rm -f {self.current_ldap}*')
    
    def get_name(self):
        full_name = self.driver.find_element_by_xpath("//ul[@class='list-unstyled puser-details-list']//h2").text
        first_name = full_name.split()[0]
        return first_name

    def run_pipeline(self, ldap):
        self.current_ldap = ldap
        self.access_url(ldap)
        self.clean_html()
        self.get_screenshot()
        self.add_pagebreak()
        pgbreak_file = f'{self.current_ldap}_gap.png'
        self.get_screenshot(pgbreak_file)
        self.crop_image(pgbreak_file)
        self.create_pdf(img_name = pgbreak_file, remove = True)
        
        return ldap, self.get_name()
        # self.create_archive()
    
    def quit(self):
        #dirname = np.random.randint(1000)
        #os.system(f'mkdir archive_{dirname}')
        #os.system(f'mv *zip *png *pdf archive_{dirname}')
        self.driver.quit()


import yagmail

def run(ID_to_run = []   ):
    def initialise():
        yag = yagmail.SMTP(user='', password='')
        driver = yb_processor()
        return yag, driver#yag, driver
    
    def send(ID, name):
        contents = f"""
        Hi {name},

        Hope you are doing well.

        This is Rishabh, Saunack and Saurav, your fellow graduates from the CSE Department. We've created our own version of the yearbook modelled after the Yearbook webpage and wanted to share your page with you as well. The web interface was really nice, so we thought of using it directly to generate PDFs. We have taken some liberties with the design and hope that the end result is to your taste.

        In this mail, you will find a PNG and a PDF file. The PNG file is a modified screenshot of the webpage and the PDF file is, well, a PDF copy of the same with proper margins.

        If you need to contact us regarding any issues, please mail us back on our accounts ({{rishabhrj}}, {{krsrv}} or {{krsaunack}} @cse.iitb.ac.in respectively).

        For those interested, the code is stored <a href="https://github.com/krsrv/sarc-yearbook">here</a>.

        Regards,
        Rishabh, Saunack, Saurav
        2016 B. Tech. CSE
        IITB

        PS: We had stored only a subset of the yearbook website, so the mail could be sent to only 558 out of 900+ students.
        """
        subject = 'Web generated SARC Yearbook'
        yag.send(to=f'{ID}@iitb.ac.in',
                 subject=subject,
                 contents=contents,
                 attachments=[f"{ID}.png", f"{ID}.pdf"],
                 headers={
                    "From": "Yearbook Delivery<experkumar@gmail.com>",
                    "Reply-To": "rishabhrj@cse.iitb.ac.in, krsrv@cse.iitb.ac.in, krsaunack@cse.iitb.ac.in",
                }
        )
    
    yag, yb = initialise()
    
    ID_list = []
    error_list = []
    passed_list = []
    
    count = 0
    
    def process(ID):
        nonlocal count,ID_list,error_list, passed_list
        if ID in ID_list:
            return
        ID_list.append(ID)
        try:
            _, name = yb.run_pipeline(ID)
            count += 1
            send(ID, name)
            passed_list.append(ID)
            print(count,ID)
        except Exception as ex:
            error_list.append(ID)
            print('ERROR',ID)
            print(ex)
            return

    if len(ID_to_run) == 0:
        for subdir, dirs, files in os.walk('../Yearbook/merged'):
            if 'student' in subdir:
                folder = subdir[2:]
                ID = subdir.split('-')[-1]
                process(ID)
    else:
        for ID in ID_to_run:
            process(ID)
    
    yb.quit()
    return passed_list, error_list

#checked = json.load(open('log_1.json'))

# passed_list, error_list = run([160050054,160040022,160020020,160010033])
passed_list, error_list = run([160050057])
file_list = {'error':error_list, 'passed':passed_list}
print("IDs served ",passed_list)
print("Error in sending to ", error_list)

with open('log_2.json','w') as f:
    f.write(json.dumps(file_list))
