#!/usr/bin/python3

import contextlib
import json
import sys
import smart_open


ngram_yearly_total = {
    1800: 69709030,
    1801: 38404622,
    1802: 52673580,
    1803: 53656522,
    1804: 54314367,
    1805: 79052464,
    1806: 46368282,
    1807: 64318031,
    1808: 33941253,
    1809: 13141808,
    1810: 14738921,
    1811: 19428616,
    1812: 24775632,
    1813: 51712363,
    1814: 39887047,
    1815: 30826735,
    1816: 29908078,
    1817: 47111396,
    1818: 53583626,
    1819: 59995366,
    1820: 73059408,
    1821: 76720526,
    1822: 65370035,
    1823: 40364329,
    1824: 47093298,
    1825: 53357160,
    1826: 84051504,
    1827: 76772291,
    1828: 78503005,
    1829: 122190378,
    1830: 90541976,
    1831: 74967449,
    1832: 86936062,
    1833: 72557770,
    1834: 77795774,
    1835: 81440896,
    1836: 100065884,
    1837: 77515189,
    1838: 94969684,
    1839: 99259140,
    1840: 143535065,
    1841: 153739451,
    1842: 147422759,
    1843: 157704942,
    1844: 219088275,
    1845: 260707569,
    1846: 241089780,
    1847: 267707387,
    1848: 239127548,
    1849: 234098328,
    1850: 279068978,
    1851: 317436330,
    1852: 325297322,
    1853: 307116458,
    1854: 270726313,
    1855: 258265972,
    1856: 243392563,
    1857: 273584557,
    1858: 271957057,
    1859: 256644234,
    1860: 255789055,
    1861: 270749052,
    1862: 275628182,
    1863: 292292994,
    1864: 284737192,
    1865: 287152538,
    1866: 265377475,
    1867: 247614283,
    1868: 231261725,
    1869: 250887635,
    1870: 278638059,
    1871: 230461867,
    1872: 289693566,
    1873: 248092517,
    1874: 250636169,
    1875: 278206776,
    1876: 339615599,
    1877: 357245290,
    1878: 348560201,
    1879: 242941925,
    1880: 240660336,
    1881: 227398363,
    1882: 248886488,
    1883: 260771543,
    1884: 256693734,
    1885: 248081225,
    1886: 248270971,
    1887: 271647351,
    1888: 273828335,
    1889: 294678104,
    1890: 301797926,
    1891: 245138124,
    1892: 275085024,
    1893: 247203785,
    1894: 262629567,
    1895: 228655586,
    1896: 266205996,
    1897: 272666963,
    1898: 283490196,
    1899: 291793084,
    1900: 355517487,
    1901: 317786424,
    1902: 345934853,
    1903: 352084451,
    1904: 336065227,
    1905: 406282972,
    1906: 383594095,
    1907: 541328386,
    1908: 447495807,
    1909: 345701393,
    1910: 544265304,
    1911: 451473513,
    1912: 484279901,
    1913: 478478670,
    1914: 476620665,
    1915: 461373830,
    1916: 481225832,
    1917: 482812239,
    1918: 493041639,
    1919: 480132804,
    1920: 570813760,
    1921: 482494691,
    1922: 471814107,
    1923: 372552086,
    1924: 343588967,
    1925: 401537210,
    1926: 376563045,
    1927: 392913594,
    1928: 453168699,
    1929: 472912695,
    1930: 525941436,
    1931: 400172355,
    1932: 395892719,
    1933: 420833413,
    1934: 410845765,
    1935: 479970447,
    1936: 467527771,
    1937: 452942737,
    1938: 501784714,
    1939: 542741801,
    1940: 544438070,
    1941: 561398611,
    1942: 609880267,
    1943: 611589682,
    1944: 666848450,
    1945: 728237110,
    1946: 836227344,
    1947: 738743597,
    1948: 743450694,
    1949: 742711124,
    1950: 779575576,
    1951: 744619232,
    1952: 809811465,
    1953: 849013147,
    1954: 846424226,
    1955: 838139836,
    1956: 937891673,
    1957: 916306655,
    1958: 992812955,
    1959: 978000225,
    1960: 1148913637,
    1961: 1084989359,
    1962: 1106245259,
    1963: 1217132054,
    1964: 1256336626,
    1965: 1254378341,
    1966: 1250491012,
    1967: 1319126751,
    1968: 1365954206,
    1969: 1311843764,
    1970: 1268757950,
    1971: 1295630286,
    1972: 1366822584,
    1973: 1479377709,
    1974: 1483439755,
    1975: 1477016168,
    1976: 1363958263,
    1977: 1384328716,
    1978: 1420434294,
    1979: 1452398535,
    1980: 1550150127,
    1981: 1609338571,
    1982: 1623429235,
    1983: 1622247680,
    1984: 1664935886,
    1985: 1674206190,
    1986: 1665888218,
    1987: 1624937252,
    1988: 1849581533,
    1989: 1767329499,
    1990: 1719694138,
    1991: 1753609423,
    1992: 1873910721,
    1993: 1807530911,
    1994: 1881910537,
    1995: 1846856664,
    1996: 1985991298,
    1997: 2147425504,
    1998: 2228406970,
    1999: 2337504837,
    2000: 2403992411,
    2001: 2362023372,
    2002: 2334436785,
    2003: 2406890023,
    2004: 2519498092,
    2005: 2630960535,
    2006: 2557488008,
    2007: 2264386152,
    2008: 1771681993,
    2009: 1423479211,
    2010: 1339543555,
    2011: 1482893290,
    2012: 1750602692,
    2013: 1639989262,
    2014: 2045981459,
    2015: 1967967331,
    2016: 1930096425,
    2017: 1889663183,
    2018: 1868364503,
    2019: 1658430062,
}

@contextlib.contextmanager
def open(filename, *args, **nargs):
    """ like smart_open, but treat empty filenames or - as stdin/out """
    if not filename or filename == "-":
        mode = args[0] if args else nargs.get("mode")
        if mode and "w" in mode:
            yield sys.stdout
        else:
            yield sys.stdin
    else:
        yield smart_open.open(filename, *args, **nargs)


def summarize_line(line, min_year=0, max_year=0, normalize=False):
    year_found = not min_year
    items = line.split('\t')
    total = 0
    for year_item in items[1:]:
        year = int(year_item[:4])

        if not year_found:
            if year <= min_year:
                continue
            year_found = True

        if max_year and year > max_year:
            break

        _, use_count, source_count = year_item.split(",")
        use_count = int(use_count)
        if normalize:
#            print(items[0], use_count, ngram_yearly_total[year], int(use_count/ngram_yearly_total[year] * 1000000))
            use_count = int(use_count/ngram_yearly_total[year] * 1000000000)

        total += use_count

    return items[0], total

def process(infilename, outfilename, min_total=0, min_year=0, limit=0, normalize=False):
    with open(outfilename, "wt") as outfile:
        with open(infilename, "rt") as fh:
            for count, line in enumerate(fh):
                if limit and count > limit:
                    break
                ngram, total = summarize_line(line, min_year, normalize=normalize)
                if total > min_total:
                    outfile.write(f"{ngram}\t{total}\n")

def lambda_handler(event, context):

    process(event["infile"], event["outfile"], event.get("min_total", 0), event.get("min_year", 0), event.get("limit", 0), event.get("normalize"))

    return {
        'statusCode': 200,
        'body': json.dumps(f'Processed {event["infile"]} -> {event["outfile"]}')
    }

if __name__ == "__main__":

    import argparse

    parser = argparse.ArgumentParser(description="Summarize ngram usage")
    parser.add_argument("infile", help="read data from url")
    parser.add_argument("--outfile", "-o", help="read data from file")
    parser.add_argument("--min-year", type=int, help="Ignore usage before the specified year")
    parser.add_argument("--min-total", type=int, help="Only print entries with at least N uses", default=0)
    parser.add_argument("--limit", type=int, help="Limit processing to first N entries", default=0)
    parser.add_argument("--normalize", action='store_true', help="Use normalized yearly data instead of absolute values", default=0)

    args = parser.parse_args()

    lambda_handler(vars(args), None)
