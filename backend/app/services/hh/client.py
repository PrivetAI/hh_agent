import httpx
import os
import logging
import json
from fastapi import HTTPException
from striprtf.striprtf import rtf_to_text
from typing import Optional, Dict, Any, List
from ...core.config import settings

logger = logging.getLogger(__name__)

class HHClient:
    def __init__(self):
        self.base_url = "https://api.hh.ru"
        
        # Проверяем наличие credentials
        if not settings.HH_CLIENT_ID or not settings.HH_CLIENT_SECRET:
            logger.error(f"HH credentials missing! client_id: {bool(settings.HH_CLIENT_ID)}, client_secret: {bool(settings.HH_CLIENT_SECRET)}")
    
    def _log_resume_section(self, section_name: str, data: Any, resume_id: str = None) -> None:
        """Детальное логирование секции резюме"""
        prefix = f"[Resume {resume_id}] " if resume_id else ""
        
        if data is None:
            logger.info(f"{prefix}Section '{section_name}': None")
            return
            
        if isinstance(data, list):
            logger.info(f"{prefix}Section '{section_name}': {len(data)} items")
            for i, item in enumerate(data):
                logger.info(f"{prefix}  [{i}] {json.dumps(item, ensure_ascii=False, indent=2)}")
        elif isinstance(data, dict):
            logger.info(f"{prefix}Section '{section_name}': {json.dumps(data, ensure_ascii=False, indent=2)}")
        else:
            logger.info(f"{prefix}Section '{section_name}': {data}")
    
    def _log_resume_structure(self, resume: Dict[str, Any]) -> None:
        """Логирование полной структуры резюме по секциям"""
        resume_id = resume.get('id', 'unknown')
        logger.info(f"=== RESUME STRUCTURE ANALYSIS [{resume_id}] ===")
        
        # Основные поля
        basic_fields = ['id', 'title', 'status', 'access', 'created_at', 'updated_at', 'next_publish_at']
        for field in basic_fields:
            if field in resume:
                logger.info(f"[Resume {resume_id}] {field}: {resume[field]}")
        
        # Персональная информация
        personal_fields = ['first_name', 'last_name', 'middle_name', 'age', 'gender', 'birth_date']
        personal_data = {field: resume.get(field) for field in personal_fields if field in resume}
        if personal_data:
            self._log_resume_section('personal_info', personal_data, resume_id)
        
        # Контактная информация
        if 'contact' in resume:
            self._log_resume_section('contact', resume['contact'], resume_id)
        
        # Локация
        if 'area' in resume:
            self._log_resume_section('area', resume['area'], resume_id)
        
        # Желаемая должность и зарплата
        if 'salary' in resume:
            self._log_resume_section('salary', resume['salary'], resume_id)
        
        # Специализации
        if 'specialization' in resume:
            self._log_resume_section('specialization', resume['specialization'], resume_id)
        
        # Опыт работы
        if 'experience' in resume:
            self._log_resume_section('experience', resume['experience'], resume_id)
        
        # Образование
        if 'education' in resume:
            self._log_resume_section('education', resume['education'], resume_id)
        
        # Языки
        if 'language' in resume:
            self._log_resume_section('languages', resume['language'], resume_id)
        
        # Навыки
        if 'skill_set' in resume:
            self._log_resume_section('skills', resume['skill_set'], resume_id)
        
        # Дополнительные поля
        additional_fields = [
            'citizenship', 'work_ticket', 'travel_time', 'recommendation', 
            'resume_locale', 'certificate', 'driver_license_types', 
            'has_vehicle', 'hidden_fields', 'owner', 'negotiations_history',
            'download', 'alternate_url', 'can_publish_or_update'
        ]
        
        for field in additional_fields:
            if field in resume:
                self._log_resume_section(field, resume[field], resume_id)
        
        # Проверяем наличие полнотекстовой версии
        if 'full_text' in resume:
            text_length = len(resume['full_text']) if resume['full_text'] else 0
            logger.info(f"[Resume {resume_id}] full_text: {text_length} characters")
            if text_length > 0:
                # Логируем первые 500 символов полного текста
                preview = resume['full_text'][:500]
                logger.info(f"[Resume {resume_id}] full_text preview: {preview}...")
        
        logger.info(f"=== END RESUME STRUCTURE [{resume_id}] ===")
    
    def _log_rtf_content(self, rtf_content: str, resume_id: str) -> None:
        """Детальное логирование RTF контента"""
        logger.info(f"=== RTF CONTENT ANALYSIS [{resume_id}] ===")
        logger.info(f"[Resume {resume_id}] RTF raw length: {len(rtf_content)} characters")
        
        # Логируем первые 1000 символов RTF
        rtf_preview = rtf_content[:1000]
        logger.info(f"[Resume {resume_id}] RTF preview: {rtf_preview}...")
        
        # Проверяем RTF заголовки и кодировку
        rtf_lines = rtf_content.split('\n')[:10]  # Первые 10 строк
        for i, line in enumerate(rtf_lines):
            logger.info(f"[Resume {resume_id}] RTF line {i}: {line}")
        
        # Пытаемся извлечь текст и логируем результат
        try:
            plain_text = rtf_to_text(rtf_content)
            logger.info(f"[Resume {resume_id}] RTF->Text conversion successful, length: {len(plain_text)}")
            
            # Логируем первые 500 символов извлеченного текста
            text_preview = plain_text[:500]
            logger.info(f"[Resume {resume_id}] Extracted text preview: {text_preview}...")
            
        except Exception as e:
            logger.error(f"[Resume {resume_id}] RTF->Text conversion failed: {str(e)}")
        
        logger.info(f"=== END RTF CONTENT [{resume_id}] ===")

    async def get_dictionaries(self):
        """Get HH dictionaries"""
        async with httpx.AsyncClient() as client:
            url = f"{self.base_url}/dictionaries"
            logger.info(f"GET {url}")
            
            response = await client.get(url)
            logger.info(f"Response: {response.status_code}, size: {len(response.content)} bytes")
            
            response.raise_for_status()
            return response.json()
    
    async def get_areas(self):
        """Get areas (cities/regions)"""
        async with httpx.AsyncClient() as client:
            url = f"{self.base_url}/areas"
            logger.info(f"GET {url}")
            
            response = await client.get(url)
            logger.info(f"Response: {response.status_code}, size: {len(response.content)} bytes")
            
            response.raise_for_status()
            return response.json()
    
    async def revoke_hh_token(self, access_token: str):
        """Отзыв токена HH"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.delete(
                    "https://api.hh.ru/oauth/token",
                    headers={"Authorization": f"Bearer {access_token}"}
                )
                return response.status_code == 204
        except Exception as e:
            logger.error(f"Error revoking token: {e}")
            return False
    
    async def exchange_code_for_token(self, code: str) -> dict:
        """Exchange OAuth code for access token"""
        async with httpx.AsyncClient() as client:
            url = "https://hh.ru/oauth/token"
            
            # Логируем полный код для отладки
            logger.info(f"Exchanging code: {code} (length: {len(code)})")
            
            if len(code) < 10:
                logger.error(f"Code seems too short: {code}")
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid authorization code: too short ({len(code)} chars)"
                )
            
            data = {
                "grant_type": "authorization_code",
                "client_id": settings.HH_CLIENT_ID,
                "client_secret": settings.HH_CLIENT_SECRET,
                "code": code,
                "redirect_uri": settings.FRONTEND_URL
            }
            
            logger.info(f"POST {url}, client_id: {settings.HH_CLIENT_ID}, redirect_uri: {settings.FRONTEND_URL}")
            
            response = await client.post(url, data=data)
            
            logger.info(f"Token exchange response: {response.status_code}")
            
            if response.status_code != 200:
                error_data = response.json()
                logger.error(f"Token exchange failed: {error_data}")
                raise HTTPException(
                    status_code=400,
                    detail=f"HH OAuth error: {error_data.get('error_description', error_data.get('error', 'Unknown error'))}"
                )
            
            data = response.json()
            logger.info(f"Token response keys: {list(data.keys())}")
            
            # Логируем важные поля
            if 'scope' in data:
                logger.info(f"Granted scopes: {data['scope']}")
            if 'token_type' in data:
                logger.info(f"Token type: {data['token_type']}")
            
            if "access_token" not in data:
                logger.error(f"No access_token in response: {data}")
                raise HTTPException(
                    status_code=400,
                    detail="Invalid response from HH: no access_token"
                )
            
            logger.info(f"Got access_token (length: {len(data['access_token'])}), expires_in: {data.get('expires_in')}")
            
            # Проверяем, есть ли необходимые права
            if 'scope' in data and data['scope']:
                scopes = data['scope'].split()
                logger.info(f"Application has following scopes: {scopes}")
                
                # Проверяем минимально необходимые права
                required_scopes = ['me', 'resumes']
                missing_scopes = [s for s in required_scopes if s not in scopes]
                if missing_scopes:
                    logger.warning(f"Missing required scopes: {missing_scopes}")
                    logger.warning("Please check application permissions at https://dev.hh.ru/admin")
            
            return data
    
    async def refresh_access_token(self, refresh_token: str) -> dict:
        """Refresh access token using refresh token"""
        async with httpx.AsyncClient() as client:
            url = "https://hh.ru/oauth/token"
            logger.info(f"POST {url}, params: grant_type=refresh_token")
            
            response = await client.post(
                url,
                data={
                    "grant_type": "refresh_token",
                    "refresh_token": refresh_token
                }
            )
            
            logger.info(f"Response: {response.status_code}")
            
            if response.status_code != 200:
                error_data = response.json()
                raise HTTPException(
                    status_code=400,
                    detail=f"Token refresh error: {error_data.get('error_description', 'Unknown error')}"
                )
            
            return response.json()
    
    async def get_user_info(self, token: str) -> dict:
        """Get user information"""
        async with httpx.AsyncClient() as client:
            url = f"{self.base_url}/me"
            headers = {
                "Authorization": f"Bearer {token}",
                "User-Agent": "HH Job Application API/1.0"
            }
            
            logger.info(f"GET {url}")
            logger.info(f"Token length: {len(token)}")
            logger.info(f"Token first 20 chars: {token[:20]}...")
            logger.info(f"Headers being sent: {headers}")
            
            response = await client.get(url, headers=headers)
            
            logger.info(f"User info response: {response.status_code}")
            logger.info(f"Response headers: {dict(response.headers)}")
            
            if response.status_code != 200:
                error_detail = ""
                try:
                    error_data = response.json()
                    logger.error(f"HH API error response JSON: {error_data}")
                    
                    # Детальный разбор ошибки HH API
                    if isinstance(error_data, dict):
                        error_type = error_data.get('error', 'unknown')
                        error_desc = error_data.get('error_description', error_data.get('description', 'No description'))
                        error_detail = f": {error_type} - {error_desc}"
                        
                        # Специальная обработка для известных ошибок
                        if error_type == 'token_revoked':
                            logger.error("Token was revoked!")
                        elif error_type == 'token_expired':
                            logger.error("Token has expired!")
                        elif 'oauth_authorize' in str(error_desc):
                            logger.error("Application needs additional authorization!")
                            logger.error("Check app permissions at https://dev.hh.ru/admin")
                    else:
                        error_detail = f": {error_data}"
                except Exception as json_error:
                    logger.error(f"Failed to parse error response as JSON: {json_error}")
                    error_text = response.text[:500]
                    error_detail = f": {error_text}"
                    logger.error(f"HH API error text: {error_text}")
                
                # Проверяем специфичные заголовки HH
                if 'X-HH-Debug' in response.headers:
                    logger.error(f"HH Debug info: {response.headers['X-HH-Debug']}")
                
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Failed to get user info from HH{error_detail}"
                )
            
            user_data = response.json()
            logger.info(f"Got user info successfully!")
            logger.info(f"User ID: {user_data.get('id')}")
            logger.info(f"User email: {user_data.get('email')}")
            logger.info(f"User name: {user_data.get('first_name')} {user_data.get('last_name')}")
            
            return user_data
    
    async def get_resumes(self, token: str, with_full_text: bool = True) -> list:
        """Get all user resumes with optional full text"""
        async with httpx.AsyncClient() as client:
            url = f"{self.base_url}/resumes/mine"
            logger.info(f"GET {url}")
            
            response = await client.get(
                url,
                headers={"Authorization": f"Bearer {token}"}
            )
            
            logger.info(f"Response: {response.status_code}")
            
            if response.status_code != 200:
                logger.error(f"Failed to get resumes list: {response.status_code}")
                return []
                
            resume_list = response.json()
            logger.info(f"Found {len(resume_list.get('items', []))} resumes")
            
            resumes = []
            
            for resume_item in resume_list.get("items", []):
                resume_id = resume_item['id']
                logger.info(f"Processing resume {resume_id}")
                
                # Get resume details
                resume_url = f"{self.base_url}/resumes/{resume_id}"
                logger.info(f"GET {resume_url}")
                
                resume_response = await client.get(
                    resume_url,
                    headers={"Authorization": f"Bearer {token}"}
                )
                logger.info(f"Resume details response: {resume_response.status_code}")
                
                if resume_response.status_code == 200:
                    resume = resume_response.json()
                    
                    # Логируем структуру резюме
                    self._log_resume_structure(resume)
                    
                    if with_full_text:
                        # Get RTF version
                        rtf_url = f"{self.base_url}/resumes/{resume_id}/download/rtf-file.rtf?type=rtf"
                        logger.info(f"GET {rtf_url}")
                        
                        rtf_response = await client.get(
                            rtf_url,
                            headers={"Authorization": f"Bearer {token}"}
                        )
                        logger.info(f"RTF response: {rtf_response.status_code}, size: {len(rtf_response.content)} bytes")
                        
                        if rtf_response.status_code == 200:
                            try:
                                # RTF файл приходит в байтах, декодируем в строку
                                rtf_content = rtf_response.content.decode('utf-8', errors='ignore')
                                
                                # Логируем RTF контент
                                self._log_rtf_content(rtf_content, resume_id)
                                
                                # Конвертируем RTF в текст
                                resume["full_text"] = rtf_to_text(rtf_content)
                                resume["rtf_raw"] = rtf_content  # Сохраняем и сырой RTF
                                
                            except Exception as e:
                                logger.error(f"Failed to parse RTF for resume {resume_id}: {e}")
                                resume["full_text"] = ""
                                resume["rtf_raw"] = ""
                        else:
                            logger.warning(f"Failed to download RTF for resume {resume_id}: {rtf_response.status_code}")
                            resume["full_text"] = ""
                            resume["rtf_raw"] = ""
                    
                    resumes.append(resume)
                else:
                    logger.error(f"Failed to get resume {resume_id} details: {resume_response.status_code}")
            
            logger.info(f"Successfully processed {len(resumes)} resumes")
            return resumes
    
    async def get_resume(self, token: str, resume_id: str = None, with_full_text: bool = True) -> dict:
        """Get specific resume by ID or first resume"""
        if resume_id:
            async with httpx.AsyncClient() as client:
                url = f"{self.base_url}/resumes/{resume_id}"
                logger.info(f"GET {url}")
                
                response = await client.get(
                    url,
                    headers={"Authorization": f"Bearer {token}"}
                )
                logger.info(f"Resume response: {response.status_code}")
                
                if response.status_code == 200:
                    resume = response.json()
                    
                    # Логируем структуру резюме
                    self._log_resume_structure(resume)
                    
                    if with_full_text:
                        # Get RTF version
                        rtf_url = f"{self.base_url}/resumes/{resume_id}/download/rtf-file.rtf?type=rtf"
                        logger.info(f"GET {rtf_url}")
                        
                        rtf_response = await client.get(
                            rtf_url,
                            headers={"Authorization": f"Bearer {token}"}
                        )
                        logger.info(f"RTF response: {rtf_response.status_code}, size: {len(rtf_response.content)} bytes")
                        
                        if rtf_response.status_code == 200:
                            try:
                                # RTF файл приходит в байтах, декодируем в строку
                                rtf_content = rtf_response.content.decode('utf-8', errors='ignore')
                                
                                # Логируем RTF контент
                                self._log_rtf_content(rtf_content, resume_id)
                                
                                # Конвертируем RTF в текст
                                resume["full_text"] = rtf_to_text(rtf_content)
                                resume["rtf_raw"] = rtf_content  # Сохраняем и сырой RTF
                                
                            except Exception as e:
                                logger.error(f"Failed to parse RTF for resume {resume_id}: {e}")
                                resume["full_text"] = ""
                                resume["rtf_raw"] = ""
                        
                    return resume
                return None
        else:
            # Get first resume for backward compatibility
            resumes = await self.get_resumes(token, with_full_text)
            return resumes[0] if resumes else None
    
    async def get_resume_sections(self, token: str, resume_id: str) -> Dict[str, Any]:
        """Get resume data organized by sections"""
        resume = await self.get_resume(token, resume_id, with_full_text=True)
        
        if not resume:
            return {}
        
        sections = {
            'basic_info': {
                'id': resume.get('id'),
                'title': resume.get('title'),
                'status': resume.get('status'),
                'created_at': resume.get('created_at'),
                'updated_at': resume.get('updated_at'),
                'alternate_url': resume.get('alternate_url')
            },
            'personal': {
                'first_name': resume.get('first_name'),
                'last_name': resume.get('last_name'),
                'middle_name': resume.get('middle_name'),
                'age': resume.get('age'),
                'gender': resume.get('gender'),
                'birth_date': resume.get('birth_date')
            },
            'contact': resume.get('contact', {}),
            'location': resume.get('area', {}),
            'salary': resume.get('salary', {}),
            'specializations': resume.get('specialization', []),
            'experience': resume.get('experience', []),
            'education': resume.get('education', {}),
            'languages': resume.get('language', []),
            'skills': resume.get('skill_set', []),
            'citizenship': resume.get('citizenship', []),
            'work_ticket': resume.get('work_ticket', []),
            'travel_time': resume.get('travel_time', {}),
            'driver_license': resume.get('driver_license_types', []),
            'has_vehicle': resume.get('has_vehicle'),
            'full_text': resume.get('full_text', ''),
            'rtf_raw': resume.get('rtf_raw', '')
        }
        
        # Логируем секции
        logger.info(f"=== RESUME SECTIONS SUMMARY [{resume_id}] ===")
        for section_name, section_data in sections.items():
            if section_data:
                if isinstance(section_data, list):
                    logger.info(f"Section '{section_name}': {len(section_data)} items")
                elif isinstance(section_data, dict):
                    logger.info(f"Section '{section_name}': {len(section_data)} fields")
                else:
                    logger.info(f"Section '{section_name}': {type(section_data).__name__}")
        
        return sections
    
    async def search_vacancies(self, token: str, params: dict) -> dict:
        """Search vacancies"""
        async with httpx.AsyncClient() as client:
            if 'per_page' not in params:
                params['per_page'] = 50
            if 'page' not in params:
                params['page'] = 0
            
            url = f"{self.base_url}/vacancies"
            logger.info(f"GET {url}, params: {params}")
            
            response = await client.get(
                url,
                params=params,
                headers={"Authorization": f"Bearer {token}"}
            )
            logger.info(f"Response: {response.status_code}, found: {response.json().get('found', 0)} vacancies")
            
            response.raise_for_status()
            return response.json()
    
    async def get_vacancy(self, token: str, vacancy_id: str) -> dict:
        """Get vacancy details"""
        async with httpx.AsyncClient() as client:
            url = f"{self.base_url}/vacancies/{vacancy_id}"
            logger.info(f"GET {url}")
            
            response = await client.get(
                url,
                headers={"Authorization": f"Bearer {token}"}
            )
            logger.info(f"Response: {response.status_code}")
            
            response.raise_for_status()
            return response.json()
    
    async def apply_to_vacancy(self, token: str, vacancy_id: str, message: str, resume_id: str = None) -> dict:
        """Apply to vacancy"""
        async with httpx.AsyncClient() as client:
            if not resume_id:
                resume = await self.get_resume(token, with_full_text=False)
                if not resume:
                    raise HTTPException(400, "No resume found")
                resume_id = resume["id"]

            url = f"{self.base_url}/negotiations"
            headers = {
                "Authorization": f"Bearer {token}",
                "User-Agent": "HH Job Application API/1.0"
            }

            # HH API требует form-data, а не JSON
            form_data = {
                "vacancy_id": vacancy_id,  # Строка, не int
                "resume_id": resume_id,
                "message": message
            }

            logger.info(f"POST {url}, vacancy_id: {vacancy_id}, resume_id: {resume_id}")
            response = await client.post(url, headers=headers, data=form_data)

            if response.status_code in [201, 204]:
                logger.info(f"Successfully applied to vacancy {vacancy_id}")
                return {"status": "success", "message": "Application sent successfully"}

            if response.status_code == 403:
                logger.warning(f"Already applied or access denied for vacancy {vacancy_id}")
                return {"status": "error", "message": "Already applied or access denied"}

            # Обработка ошибок
            error_detail = "Unknown error"
            if response.text.strip():
                try:
                    error_data = response.json()
                    error_detail = error_data.get("description", str(error_data))
                except:
                    error_detail = response.text

            logger.error(f"Apply failed: {response.status_code} - {error_detail}")
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Failed to apply: {error_detail}"
            )