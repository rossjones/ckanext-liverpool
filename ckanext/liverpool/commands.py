# -*- coding: utf-8 -*-
import datetime
import logging
import os
import sys
import requests
from StringIO import StringIO

import ckanapi
from lxml.html import fromstring
from lxml import etree

from ckan.lib.cli import CkanCommand
import slugify

class ScrapeCommand(CkanCommand):

    summary = "Scrapes some specific datasets from known URLS"
    usage = "paster scrape -c $CKAN_INI"
    max_args = 0
    min_args = 0

    def __init__(self, name):
        super(ScrapeCommand, self).__init__(name)

    def command(self):
        self._load_config()
        log = logging.getLogger(__name__)

        import ckan.model as model
        model.Session.remove()
        model.Session.configure(bind=model.meta.engine)

        print "Scraping!"
        u = UKHOScraper()
        u.scrape()

        #l = LiverpoolCCScraper()
        #l.scrape()

class Scraper(object):

    def scrape(self):
        pass

class UKHOScraper(Scraper):


    def scrape(self):
        ckan = ckanapi.RemoteCKAN("http://liverpool.servercode.co.uk", apikey="DERP")

        for x in xrange(1, 21):
            data = requests.get("http://data.gov.uk/feeds/custom.atom?q=liverpool&publisher=united-kingdom-hydrographic-office&page={}".format(x))
            if not data.status_code == 200:
                break
            print "Got page ", x
            doc = etree.parse(StringIO(data.content))

            entries = doc.xpath('//a:entry',
                    namespaces={'a': 'http://www.w3.org/2005/Atom'})
            if len(entries) == 0:
                break

            for e in entries:
                """
                <entry xmlns="http://www.w3.org/2005/Atom">
                    <title>Bathymetric Survey - 1998-08-19 - Liverpool Landing Stage</title>
                    <link href="http://data.gov.uk/dataset/34b88c3e-8f6e-4acb-b709-e42b9129c25f" rel="alternate"/>
                    <id>tag:data.gov.uk,2012:/dataset/34b88c3e-8f6e-4acb-b709-e42b9129c25f</id>
                    <summary type="html">IPR Holder: Mersey Docks and Harbour Company; Purpose: Safety of navigation; IHO Sea: Irish Sea and the St. Georges Channel - 19; Survey Start: 1998-08-19; Survey End: 1998-08-19; Primary Instrument Type: Echosounder - single beam; Primary Navigation Type: Not Known;</summary><link length="24101" href="http://data.gov.uk/api/2/rest/package/bathymetric-survey-1998-08-19-liverpool-landing-stage" type="application/json" rel="enclosure"/><updated>2015-01-27T10:37:25Z</updated><published>2015-01-27T10:37:25Z</published></entry>
                """
                link = e.xpath("a:link", namespaces={'a': 'http://www.w3.org/2005/Atom'})
                theid = link[0].get('href').split('/')[-1]
                blob = requests.get('http://data.gov.uk/api/action/package_show?id={}'.format(theid)).json()['result']

                dataset = {
                    "name": blob["name"], "title": blob["title"], "notes": blob["notes"],
                    "resources": blob["resources"], "owner_org": "united-kingdom-hydrographic-office"
                }
                ckan.action.package_create(**dataset)





class LiverpoolCCScraper(Scraper):

    def __init__(self):
        self.url = u"http://liverpool.gov.uk/council/performance-and-spending/budgets-and-finance/transparency-in-local-government/"
        self.publisher = u"liverpool-city-council"
        self.ckan = ckanapi.LocalCKAN()

    def scrape(self):
        dom = fromstring(requests.get(self.url).content)
        h3s = dom.cssselect('.bodyContent h3')
        for h3 in h3s:
            label = h3.text_content().strip()
            links = h3.getnext().cssselect('li a')

            paras = dom.cssselect('.bodyContent p')[:10]
            description = "\n\n".join(p.text_content().strip() for p in paras)
            dataset = {
                "title": u"Payments of invoices to vendors over £500 - {}".format(label),
                "notes": unicode(description),
                "owner_org": self.publisher,
                "resources": [],
                "tags": [{"name": "spending"}],
                "license_id": "uk-ogl"
            }
            for l in links:
                href = l.get('href')
                name = href.split('/')[-1]
                ext = name[name.rfind('.')+1:]
                dataset["resources"].append({
                    'url': "http://liverpool.gov.uk" + href,
                    'name': name,
                    'description': l.text_content().strip(),
                    'format': ext.upper()
                })

            dataset["name"] = u"lcc-{}".format(slugify.slugify(dataset["title"]).lower())
            try:
                pkg = self.ckan.action.package_show(id=dataset['name'])
                pkg['tags'] = dataset['tags']
                pkg['notes'] = dataset['notes']
                pkg['license_id'] = dataset['license_id']
                pkg = self.ckan.action.package_update(**pkg)
            except Exception, e:
                pkg = self.ckan.action.package_create(**dataset)




