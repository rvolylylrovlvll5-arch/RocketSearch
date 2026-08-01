#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ROCKET SEARCH — LEAKOSINT API

import requests
import json
from config import LEAKOSINT_API_KEY, LEAKOSINT_URL

def search_leakosint(query):
    """Поиск через LeakOsint API"""
    try:
        url = f"{LEAKOSINT_URL}?query={query}&api_key={LEAKOSINT_API_KEY}"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                return {
                    'source': 'LeakOsint',
                    'found': True,
                    'data': data.get('result', {}),
                    'raw': json.dumps(data, indent=2)
                }
            else:
                return {
                    'source': 'LeakOsint',
                    'found': False,
                    'data': 'Ничего не найдено',
                    'raw': ''
                }
        else:
            return {
                'source': 'LeakOsint',
                'found': False,
                'data': f'Ошибка API: {response.status_code}',
                'raw': ''
            }
    except Exception as e:
        return {
            'source': 'LeakOsint',
            'found': False,
            'data': f'Ошибка подключения: {str(e)[:50]}',
            'raw': ''
        }
