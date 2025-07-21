import httpx
import logging
from typing import Optional, Dict, List
from fastapi import HTTPException
from ...core.config import settings
from typing import Dict, Any
import asyncio

logger = logging.getLogger(__name__)

class HHClient:
    def __init__(self):
        self.base_url = "https://api.hh.ru"
        
        # Timeout settings
        self.timeout = httpx.Timeout(
            connect=30.0,  # connection timeout
            read=30.0,     # read timeout
            write=30.0,    # write timeout
            pool=30.0      # pool timeout
        )
        
        # Retry settings
        self.max_retries = settings.HH_RETRY_COUNT
        self.retry_delay = settings.HH_BATCH_DELAY  # seconds
        
        if not settings.HH_CLIENT_ID or not settings.HH_CLIENT_SECRET:
            logger.error("HH credentials missing!")
    
    async def _make_request_with_retry(self, method: str, url: str, 
                                     headers: Dict = None, params: Dict = None, 
                                     data: Dict = None, retry_count: int = 0) -> httpx.Response:
        """Make HTTP request with retry logic"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                logger.info(f"Making {method} request to {url}")
                
                if method == "GET":
                    response = await client.get(url, headers=headers, params=params)
                elif method == "POST":
                    response = await client.post(url, headers=headers, data=data)
                elif method == "DELETE":
                    response = await client.delete(url, headers=headers)
                else:
                    raise ValueError(f"Unsupported method: {method}")
                
                logger.info(f"Response status: {response.status_code}")
                return response
                
        except httpx.TimeoutException as e:
            logger.error(f"Timeout error on {url}: {e}")
            
            if retry_count < self.max_retries:
                wait_time = self.retry_delay * (retry_count + 1)
                logger.info(f"Retrying in {wait_time} seconds... (attempt {retry_count + 1}/{self.max_retries})")
                await asyncio.sleep(wait_time)
                return await self._make_request_with_retry(
                    method, url, headers, params, data, retry_count + 1
                )
            else:
                logger.error(f"Max retries exceeded for {url}")
                raise HTTPException(
                    status_code=504,
                    detail=f"Request to HH API timed out after {self.max_retries} retries"
                )
                
        except httpx.RequestError as e:
            logger.error(f"Request error on {url}: {e}")
            raise HTTPException(
                status_code=503,
                detail=f"Error connecting to HH API: {str(e)}"
            )
    
    async def get_dictionaries(self):
        response = await self._make_request_with_retry("GET", f"{self.base_url}/dictionaries")
        response.raise_for_status()
        return response.json()
    
    async def get_areas(self):
        response = await self._make_request_with_retry("GET", f"{self.base_url}/areas")
        response.raise_for_status()
        return response.json()
    
    async def revoke_hh_token(self, access_token: str):
        try:
            response = await self._make_request_with_retry(
                "DELETE",
                f"{self.base_url}/oauth/token",
                headers={"Authorization": f"Bearer {access_token}"}
            )
            return response.status_code == 204
        except Exception as e:
            logger.error(f"Error revoking token: {e}")
            return False
    
    async def exchange_code_for_token(self, code: str) -> dict:
        data = {
            "grant_type": "authorization_code",
            "client_id": settings.HH_CLIENT_ID,
            "client_secret": settings.HH_CLIENT_SECRET,
            "code": code,
            "redirect_uri": settings.FRONTEND_URL
        }
        
        response = await self._make_request_with_retry(
            "POST", 
            "https://hh.ru/oauth/token", 
            data=data
        )
        
        if response.status_code != 200:
            error_data = response.json()
            logger.error(f"Token exchange failed: {error_data}")
            raise HTTPException(
                status_code=400,
                detail=f"HH OAuth error: {error_data.get('error_description', 'Unknown error')}"
            )
        
        token_data = response.json()
        logger.info(f"Token obtained, expires_in: {token_data.get('expires_in')}")
        return token_data
    
    async def refresh_access_token(self, refresh_token: str) -> dict:
        data = {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token
        }
        
        response = await self._make_request_with_retry(
            "POST",
            "https://hh.ru/oauth/token",
            data=data
        )
        
        if response.status_code != 200:
            error_data = response.json()
            raise HTTPException(
                status_code=400,
                detail=f"Token refresh error: {error_data.get('error_description', 'Unknown error')}"
            )
        
        return response.json()
    
    async def get_user_info(self, token: str) -> dict:
        response = await self._make_request_with_retry(
            "GET",
            f"{self.base_url}/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        if response.status_code != 200:
            logger.error(f"Failed to get user info: {response.status_code}")
            raise HTTPException(
                status_code=response.status_code,
                detail="Failed to get user info from HH"
            )
        
        return response.json()
    
    async def get_resumes(self, token: str) -> List[dict]:
        headers = {"Authorization": f"Bearer {token}"}
        
        # Get resume list
        response = await self._make_request_with_retry(
            "GET",
            f"{self.base_url}/resumes/mine",
            headers=headers
        )
        
        if response.status_code != 200:
            logger.error(f"Failed to get resumes list: {response.status_code}")
            return []
        
        resume_list = response.json()
        resumes = []
        
        # Get details for each resume
        for resume_item in resume_list.get("items", []):
            try:
                resume_response = await self._make_request_with_retry(
                    "GET",
                    f"{self.base_url}/resumes/{resume_item['id']}",
                    headers=headers
                )
                
                if resume_response.status_code == 200:
                    resumes.append(resume_response.json())
            except Exception as e:
                logger.error(f"Failed to load resume {resume_item['id']}: {e}")
                continue
        
        logger.info(f"Loaded {len(resumes)} resumes")
        return resumes
    
    async def get_resume(self, token: str, resume_id: str = None) -> Optional[dict]:
        if resume_id:
            response = await self._make_request_with_retry(
                "GET",
                f"{self.base_url}/resumes/{resume_id}",
                headers={"Authorization": f"Bearer {token}"}
            )
            logger.info(f"Resume data loaded for ID: {resume_id}")
            return response.json() if response.status_code == 200 else None
        else:
            resumes = await self.get_resumes(token)
            return resumes[0] if resumes else None
    
    async def search_vacancies(self, token: str, params: dict) -> dict:
        params.setdefault('per_page', 50)
        params.setdefault('page', 0)
        
        logger.info(f"Searching vacancies with params: {params}")
        
        try:
            response = await self._make_request_with_retry(
                "GET",
                f"{self.base_url}/vacancies",
                params=params,
                headers={"Authorization": f"Bearer {token}"}
            )
            
            response.raise_for_status()
            result = response.json()
            logger.info(f"Found {result.get('found', 0)} vacancies on page {params.get('page', 0)}")
            return result
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error searching vacancies: {e}")
            # Return empty result instead of failing completely
            return {
                "items": [],
                "found": 0,
                "pages": 0,
                "per_page": params.get('per_page', 50),
                "page": params.get('page', 0)
            }
    
    async def get_vacancy(self, token: str, vacancy_id: str) -> dict:
        logger.info(f"Loading vacancy details for ID: {vacancy_id}")
        
        response = await self._make_request_with_retry(
            "GET",
            f"{self.base_url}/vacancies/{vacancy_id}",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        response.raise_for_status()
        return response.json()
    
    async def apply_to_vacancy(self, token: str, vacancy_id: str, message: str, resume_id: str = None) -> dict:
        if not resume_id:
            resume = await self.get_resume(token)
            if not resume:
                raise HTTPException(400, "No resume found")
            resume_id = resume["id"]

        form_data = {
            "vacancy_id": vacancy_id,
            "resume_id": resume_id,
            "message": message
        }

        logger.info(f"Applying to vacancy {vacancy_id} with resume {resume_id}")

        response = await self._make_request_with_retry(
            "POST",
            f"{self.base_url}/negotiations",
            headers={"Authorization": f"Bearer {token}"},
            data=form_data
        )

        if response.status_code in [201, 204]:
            logger.info(f"Successfully applied to vacancy {vacancy_id}")
            return {"status": "success", "message": "Application sent successfully"}

        if response.status_code == 403:
            logger.warning(f"Already applied or access denied for vacancy {vacancy_id}")
            return {"status": "error", "message": "Already applied or access denied"}

        # Handle errors
        try:
            error_data = response.json()
            error_detail = error_data.get("description", str(error_data))
        except:
            error_detail = response.text or "Unknown error"

        logger.error(f"Apply failed: {response.status_code} - {error_detail}")
        raise HTTPException(
            status_code=response.status_code,
            detail=f"Failed to apply: {error_detail}"
        )
        
    async def get_saved_searches(self, token: str) -> Dict[str, Any]:
        """Get user's saved searches"""
        response = await self._make_request_with_retry(
            "GET",
            f"{self.base_url}/saved_searches/vacancies",
            headers={"Authorization": f"Bearer {token}"},
            params={"per_page": 10}
        )
    
        if response.status_code != 200:
            logger.error(f"Failed to get saved searches: {response.status_code}")
            try:
                error_data = response.json()
            except:
                error_data = {"description": "Failed to parse error response"}
    
            raise HTTPException(
                status_code=response.status_code,
                detail=error_data.get('description', 'Failed to get saved searches')
            )
    
        return response.json()
        
    async def search_vacancies_by_url(self, token: str, search_url: str) -> dict:
        """Search vacancies using saved search URL"""
        logger.info(f"Searching vacancies by URL: {search_url}")
        
        try:
            response = await self._make_request_with_retry(
                "GET",
                search_url,
                headers={"Authorization": f"Bearer {token}"}
            )
            
            if response.status_code != 200:
                logger.error(f"Search by URL failed: {response.status_code}")
                response.raise_for_status()
            
            result = response.json()
            logger.info(f"Found {result.get('found', 0)} vacancies using saved search URL")
            return result
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error in search_vacancies_by_url: {e}")
            # Return empty result instead of failing completely
            return {
                "items": [],
                "found": 0,
                "pages": 0,
                "per_page": 50,
                "page": 0
            }