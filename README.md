This module is tailored for the collection of online price data. It tries to define an unified approach to scrape data systematically for all e-commerce websites.

# Overall approach/principle

Firstly, during the development of this project, we try to:

- Use Python only
- Follow good programming niceties: DRY, Unix Philosophy, etc...
- Have good documentations

Price data collection from a website generally consist of the following steps, each step should belong to a single module:

1. Send a request to main site or the sitemap page and obtain its source code
2. Collecting information of categories and subcategories webpages
3. For each sub-directory, define a method to find a block of data for each item
4. Compress and write data into databases, backup HTMLs if necessary


# Streamlined API for online-retailer price scraping

With the general procedure laid out above, this project aims for a simple and coherent approach to the tasks of online retailer scraping. For example, a scraper should look something like this:

```python
from pricescraper import PriceScraper
from categories.nested_cat import NestedCat
from items.indentify import ItemIdentify
from blocked_data.pagination import Pagination

PriceScraper.site_name = "lazada"
PriceScraper.base_url = "lazada.vn"
PriceScraper.category_identificator = NestedCat("<xpath-selector>")
PriceScraper.item_identificator = ItemIndentify("...")
PriceScraper.blocked_method = Pagination("...")

PriceScraper.deploy()
```

The following problems often arise:

- Websites populate contents using Javascript, in that case, a browser must be stimulated, using the `selenium` module
- A decent website (with decent amount of data) usually have several methods to navigate around products: paginations, "see more" buttons,...
- Sometimes popups/adverts show up, which prevent browsers to "see" data

...and some more. Recurring errors of these types force us to properly modularize our codebase and handling errors if we want to expand our data collections.

These are QoL features that should also be addressed:

- Version control of Python and package versions (currently using `pipenv`)
- Logging/debugging (currently using an implementation of the `logging` module)
- Managing multiple scrapers (currently using `tmux` and `tmuxp`)
