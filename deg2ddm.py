from typing import Tuple
import json
import requests
import random
import multiprocessing as mp
from tqdm import tqdm
from bs4 import BeautifulSoup

def deg2ddm(lat: float, lon: float) -> Tuple[str, str]:
    """Converts decimal degrees to Degrees Decimal Minutes format."""
    deg_lat, min_lat = str(abs(int(lat))).zfill(2), round(abs(lat - int(lat))*60, 5)
    deg_lon, min_lon = str(abs(int(lon))).zfill(3), round(abs(lon - int(lon))*60, 5)
    min_lat = f'{str(int(min_lat)).zfill(4 - len(deg_lat))}.{str(min_lat).split(".")[1]}'
    min_lon = f'{str(int(min_lon)).zfill(5 - len(deg_lon))}.{str(min_lon).split(".")[1]}'
    return (f'{deg_lat}{min_lat},{"N" if lat > 0 else "S"}', f'{deg_lon}{min_lon},{"E" if lon > 0 else "W"}')

def get_answer(x) -> Tuple[str,str]:
    lat, lon = x
    res = requests.get(f'http://www.hiddenvision.co.uk/ez/?dec_lat={lat}&dec_lon={lon}')
    parsed_html = BeautifulSoup(str(res.content), features='lxml')
    true_lat = parsed_html.find('input', attrs={'id': 'nmea_lat'})['value']
    true_lon = parsed_html.find('input', attrs={'id': 'nmea_lon'})['value']
    return true_lat, true_lon

def verify(num_times: int, fname: str = None):
    """Testing with the website. Only used for validation.
    num_times: how many examples to generate and testing
    fname: filename for previously saved json file
    """

    if fname:
        with open(fname, 'r') as f:
            examples = json.load(f)
        examples, true_answers = examples['examples'], examples['answers']
    else:
        examples = [(66.882115,-76.039129), (25.092267,125.987818),(56.166042,-176.45725)]  # good examples for testing padding
        for _ in range(num_times):
            # rescaling from [0,1] to proper ranges -- [-90,90] for lat, [-180,180] for lon
            lat = round(random.random() * 180 - 90, 6)
            lon = round(random.random() * 360 - 180, 6)
            examples.append((lat, lon))

        with mp.Pool(processes=2) as pool:
            with tqdm(total=len(examples)) as pbar:
                true_answers = []
                for x in pool.imap(get_answer, examples):
                    true_answers.append(x)
                    pbar.update()

        with open('examples2.json', 'w', encoding='utf-8') as f:
            json.dump({'examples': examples, 'answers': true_answers}, f)

    for (lat, lon), (true_lat, true_lon) in tqdm(zip(examples, true_answers)):
        current_lat, current_lon = deg2ddm(lat, lon)
        msg = f'Mismatch for {lat},{lon}: {current_lat}, {current_lon} but it should be {true_lat}, {true_lon}'
        assert (current_lat, current_lon) == (true_lat, true_lon), msg
    print('Everything ok!')

if __name__ == "__main__":
    verify(100, 'examples.json')
