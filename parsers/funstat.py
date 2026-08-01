#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ROCKET SEARCH — FUNSTAT API

import requests
import json
from config import FUNSTAT_API_KEY, FUNSTAT_URL

def search_funstat(query):
    """Поиск через Funstat API"""
    try:
        url = f"{FUNSTAT_URL}?query={query}&api_key={FUNSTAT_API_KEY}"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'success':
                return {
                    'source': 'Funstat',
                    'found': True,
                    'data': data.get('data', {}),
                    'raw': json.dumps(data, indent=2)
                }
            else:
                return {
                    'source': 'Funstat',
                    'found': False,
                    'data': 'Ничего не найдено',
                    'raw': ''
                }
        else:
            return {
                'source': 'Funstat',
                'found': False,
                'data': f'Ошибка API: {response.status_code}',
                'raw': ''
            }
    except Exception as e:
        return {
            'source': 'Funstat',
            'found': False,
            'data': f'Ошибка подключения: {str(e)[:50]}',
            'raw': ''
        }
