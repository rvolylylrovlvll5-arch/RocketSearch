#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ROCKET SEARCH — VEKTOR API

import requests
import json
from config import VEKTOR_API_KEY, VEKTOR_URL

def search_vektor(query):
    """Поиск через Vektor API"""
    try:
        url = f"{VEKTOR_URL}?query={query}&api_key={VEKTOR_API_KEY}"
        response = requests.get(url, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success') or data.get('status') == 'ok':
                return {
                    'source': 'Vektor',
                    'found': True,
                    'data': data.get('result', data.get('data', {})),
                    'raw': json.dumps(data, indent=2)
                }
            else:
                return {
                    'source': 'Vektor',
                    'found': False,
                    'data': 'Ничего не найдено',
                    'raw': ''
                }
        else:
            return {
                'source': 'Vektor',
                'found': False,
                'data': f'Ошибка API: {response.status_code}',
                'raw': ''
            }
    except Exception as e:
        return {
            'source': 'Vektor',
            'found': False,
            'data': f'Ошибка подключения: {str(e)[:50]}',
            'raw': ''
        }
