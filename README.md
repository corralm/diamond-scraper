# About
DiamondScraper is a simple Python web scraper for [BrilliantEarth.com](https://www.brilliantearth.com). It scrapes data for both its natural and lab created diamond selection and writes it to a CSV file.  

## Inspiration
Buying a diamond can be frustrating and expensive.

I built DiamondScraper to create a dataset of natural and lab-created diamonds to demystify the value of the 4 Cs – cut, color, clarity, carat.

## Requirements
- Firefox browser & [geckodriver](https://selenium-python.readthedocs.io/installation.html#drivers)
- pip install `gazpacho=1.1`
- conda install `pandas=1.1.3`
- conda install `selenium=3.141.0`

## Usage
1. Clone this repo
2. Move to the `DiamondScraper` directory
3. Run `scraper.py`

There is also a script `processing.py` to cast categorical data types for a DataFrame.

## Attributes
|   Attribute     |   Description                                                                            |   Data Type           |
|-----------------|------------------------------------------------------------------------------------------|-----------------------|
|   id            |   Diamond identification number provided by Brilliant Earth                              |   int                 |
|   url           |   URL for the diamond details page                                                       |   string              |
|   shape         |   External geometric appearance of a diamond                                             |   string/categorical  |
|   price         |   Price in U.S. dollars                                                                  |   int                 |
|   carat         |   Unit of measurement used to describe the weight of a diamond                           |   float               |
|   cut           |   Facets, symmetry, and reflective qualities of a diamond                                |   string/categorical  |
|   color         |   Natural color or lack of color visible within a diamond, based on the GIA grade scale  |   string/categorical  |
|   clarity       |   Visibility of natural microscopic inclusions and imperfections within a diamond        |   string/categorical  |
|   report        |   Diamond certificate or grading report provided by an independent gemology lab          |   string              |
|   type          |   Natural or lab created diamonds                                                        |   string              |
|   date_fetched  |   Date the data was fetched                                                              |   date                |

## Meta
Author: Miguel Corral Jr.  
Email: corraljrmiguel@gmail.com  
LinkedIn: https://www.linkedin.com/in/iMiguel 
GitHub: https://github.com/corralm

Distributed under the GNU General Public License v3.0. See [LICENSE](./LICENSE) for more information.
