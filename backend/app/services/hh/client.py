import httpx
import os
import logging
from fastapi import HTTPException
from striprtf.striprtf import rtf_to_text

logger = logging.getLogger(__name__)

class HHClient:
    def __init__(self):
        self.client_id = os.getenv("HH_CLIENT_ID")
        self.client_secret = os.getenv("HH_CLIENT_SECRET")
        self.frontend_url = os.getenv("FRONTEND_URL")
        self.base_url = "https://api.hh.ru"
        
        # Проверяем наличие credentials
        if not self.client_id or not self.client_secret:
            logger.error(f"HH credentials missing! client_id: {bool(self.client_id)}, client_secret: {bool(self.client_secret)}")
    
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
    async def revoke_hh_token(access_token: str):
        """Отзыв токена HH"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.delete(
                    "https://api.hh.ru/oauth/token",
                    headers={"Authorization": f"Bearer {access_token}"}
                )
                return response.status_code == 204
        except Exception as e:
            print(f"Error revoking token: {e}")
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
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "code": code,
                "redirect_uri": self.frontend_url
            }
            
            logger.info(f"POST {url}, client_id: {self.client_id}, redirect_uri: {self.frontend_url}")
            
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
    
    async def get_resumes(self, token: str) -> list:
        """Get all user resumes with full text"""
        async with httpx.AsyncClient() as client:
            url = f"{self.base_url}/resumes/mine"
            logger.info(f"GET {url}")
            
            response = await client.get(
                url,
                headers={"Authorization": f"Bearer {token}"}
            )
            
            logger.info(f"Response: {response.status_code}")
            
            if response.status_code != 200:
                return []
                
            resume_list = response.json()
            resumes = []
            
            for resume_item in resume_list.get("items", []):
                # Get resume details
                resume_url = f"{self.base_url}/resumes/{resume_item['id']}"
                logger.info(f"GET {resume_url}")
                
                resume_response = await client.get(
                    resume_url,
                    headers={"Authorization": f"Bearer {token}"}
                )
                logger.info(f"Response: {resume_response.status_code}")
                
                if resume_response.status_code == 200:
                    resume = resume_response.json()
                    
                    # Get plaintext version
                    text_url = f"{self.base_url}/resumes/{resume_item['id']}/download/rtf-file.rtf?type=rtf"
                    logger.info(f"GET {text_url}")
                    
                    rtf_response = await client.get(
                        text_url,
                        headers={"Authorization": f"Bearer {token}"}
                    )
                    logger.info(f"Response: {rtf_response.status_code}, size: {len(rtf_response.content)} bytes")
                    
                    if rtf_response.status_code == 200:
                        try:
                            # RTF файл приходит в байтах, декодируем в строку
                            rtf_content = rtf_response.content.decode('utf-8', errors='ignore')
                            resume["full_text"] = rtf_to_text(rtf_content)
                        except Exception as e:
                            logger.error(f"Failed to parse RTF: {e}")
                            resume["full_text"] = ""
                    
                    resumes.append(resume)
            
            return resumes
    
    async def get_resume(self, token: str, resume_id: str = None) -> dict:
        """Get specific resume by ID or first resume"""
        if resume_id:
            async with httpx.AsyncClient() as client:
                url = f"{self.base_url}/resumes/{resume_id}"
                logger.info(f"GET {url}")
                
                response = await client.get(
                    url,
                    headers={"Authorization": f"Bearer {token}"}
                )
                logger.info(f"Response: {response.status_code}")
                
                if response.status_code == 200:
                    resume = response.json()
                    
                    # Get plaintext version
                    text_url = f"{self.base_url}/resumes/{resume_id}/download/rtf-file.rtf?type=rtf"
                    logger.info(f"GET {text_url}")
                    
                    rtf_response = await client.get(
                        text_url,
                        headers={"Authorization": f"Bearer {token}"}
                    )
                    logger.info(f"Response: {rtf_response.status_code}, size: {len(rtf_response.content)} bytes")
                    
                    if rtf_response.status_code == 200:
                        try:
                            # RTF файл приходит в байтах, декодируем в строку
                            rtf_content = rtf_response.content.decode('utf-8', errors='ignore')
                            resume["full_text"] = rtf_to_text(rtf_content)
                        except Exception as e:
                            logger.error(f"Failed to parse RTF: {e}")
                            resume["full_text"] = ""
                        
                    return resume
                return None
        else:
            # Get first resume for backward compatibility
            resumes = await self.get_resumes(token)
            return resumes[0] if resumes else None
    
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
        async with httpx.AsyncClient() as client:
            if not resume_id:
                resume = await self.get_resume(token)
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

            response = await client.post(url, headers=headers, data=form_data)

            if response.status_code in [201, 204]:
                return {"status": "success", "message": "Application sent successfully"}

            if response.status_code == 403:
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