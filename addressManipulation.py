import pandas as pd
from selenium import webdriver
import time


df = pd.read_csv('newwest_addresses.csv')

# Using Chrome to access web
driver = webdriver.Chrome('./chromedriver')# Open the website

# driver.get('https://canvas.case.edu')

driver.get('https://app.my-waste.mobi/CA/BC/New_Westminster/Schedule?resize')

# Clicking schedule button
driver.find_element_by_xpath('//*[@id="features"]/div/div[2]/div[2]/button[1]').click()

# Clicking that ok button
# okButton = driver.find_element_by_xpath('/html/body/div[5]/div[2]/div/div[4]/div[2]/button')
#
# okButton.click()

# Getting address text box
addressBox = driver.find_element_by_xpath('/html/body/div[3]/div[4]/div[5]/div/div[4]/div/div[1]/div/input[2]')
#
# # Entering Address
# addressBox.send_keys('1430 Nanaimo Street, New Westminster, British Columbia, Canada')
addressBox.send_keys('105 Ovens Avenue, New Westminster, BC, Canada')


driver.find_element_by_id("locationGoogle").send_keys("n")
time.sleep(5)
l = driver.find_element_by_class_name("pac-item")
print(l)
#
# driver.find_element_by_id("locationGoogle").sendKeys("n");
# addressBox.click()
# time.sleep(2)
# #
# # # Clicking the confirm address box
# driver.find_element_by_xpath('//*[@id="confirm-location-button"]').click()
# #
# # Getting the zone
# zone = driver.find_element_by_xpath('//*[@id="body-zone-confirmation"]/div/div[1]/p[1]/span[2]')
# print(zone.get_attribute("innerText"))



