import httpx
import logging
from typing import Optional, Dict, List, Any
from fastapi import HTTPException
from ...core.config import settings
from ...core.http_client import HTTPClient

logger = logging.getLogger(__name__)

class HHClient:
    def __init__(self):
        self.base_url = "https://api.hh.ru"
        
        if not settings.HH_CLIENT_ID or not settings.HH_CLIENT_SECRET:
            logger.error("HH credentials missing!")
    
    def _get_auth_headers(self, token: str) -> Dict[str, str]:
        """Get authorization headers with token"""
        return {"Authorization": f"Bearer {token}"}
    
    async def _make_request(
        self, 
        method: str, 
        url: str, 
        token: str = None,
        params: Dict = None,
        data: Dict = None,
        json: Dict = None
    ) -> httpx.Response:
        """Make HTTP request with proper error handling"""
        client = HTTPClient.get_client()
        
        headers = {}
        if token:
            headers.update(self._get_auth_headers(token))
        
        try:
            if method.upper() == "GET":
                response = await client.get(url, params=params, headers=headers)
            elif method.upper() == "POST":
                response = await client.post(url, data=data, json=json, headers=headers)
            elif method.upper() == "DELETE":
                response = await client.delete(url, headers=headers)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            return response
        except httpx.TimeoutException:
            logger.error(f"Timeout for {method} {url}")
            raise HTTPException(status_code=408, detail="Request timeout")
        except httpx.ConnectError:
            logger.error(f"Connection error for {method} {url}")
            raise HTTPException(status_code=503, detail="Service unavailable")
        except Exception as e:
            logger.error(f"Request failed for {method} {url}: {e}")
            raise HTTPException(status_code=500, detail="Internal server error")
    
    async def get_dictionaries(self):
        response = await self._make_request("GET", f"{self.base_url}/dictionaries")
        response.raise_for_status()
        return response.json()
    
    async def get_areas(self):
        response = await self._make_request("GET", f"{self.base_url}/areas")
        response.raise_for_status()
        return response.json()
    
    async def revoke_hh_token(self, access_token: str):
        try:
            response = await self._make_request(
                "DELETE", 
                f"{self.base_url}/oauth/token",
                token=access_token
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
        
        # Use temporary client for OAuth without default headers
        async with HTTPClient.get_temp_client() as client:
            response = await client.post("https://hh.ru/oauth/token", data=data)
            
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
        
        # Use temporary client for OAuth without default headers
        async with HTTPClient.get_temp_client() as client:
            response = await client.post("https://hh.ru/oauth/token", data=data)
            
            if response.status_code != 200:
                error_data = response.json()
                raise HTTPException(
                    status_code=400,
                    detail=f"Token refresh error: {error_data.get('error_description', 'Unknown error')}"
                )
            
            return response.json()
    
    async def get_user_info(self, token: str) -> dict:
        response = await self._make_request("GET", f"{self.base_url}/me", token=token)
        
        if response.status_code != 200:
            logger.error(f"Failed to get user info: {response.status_code}")
            raise HTTPException(
                status_code=response.status_code,
                detail="Failed to get user info from HH"
            )
        
        return response.json()
    
    async def get_resumes(self, token: str) -> List[dict]:
        # Get resume list
        response = await self._make_request(
            "GET", 
            f"{self.base_url}/resumes/mine", 
            token=token
        )
        
        if response.status_code != 200:
            logger.error(f"Failed to get resumes list: {response.status_code}")
            return []
        
        resume_list = response.json()
        resumes = []
        
        # Get details for each resume
        for resume_item in resume_list.get("items", []):
            resume_response = await self._make_request(
                "GET",
                f"{self.base_url}/resumes/{resume_item['id']}", 
                token=token
            )
            
            if resume_response.status_code == 200:
                resumes.append(resume_response.json())
        
        logger.info(f"Loaded {len(resumes)} resumes")
        return resumes
    
    async def get_resume(self, token: str, resume_id: str = None) -> Optional[dict]:
        if resume_id:
            response = await self._make_request(
                "GET",
                f"{self.base_url}/resumes/{resume_id}",
                token=token
            )
            logger.info(f"Resume response status: {response.status_code}")
            return response.json() if response.status_code == 200 else None
        else:
            resumes = await self.get_resumes(token)
            return resumes[0] if resumes else None
    
    async def search_vacancies(self, token: str, params: dict) -> dict:
        response = await self._make_request(
            "GET",
            f"{self.base_url}/vacancies",
            token=token,
            params=params
        )
        
        result = response.json()
        logger.info(f"Found {result.get('found', 0)} vacancies")
        response.raise_for_status()
        return result
    
    async def get_vacancy(self, token: str, vacancy_id: str) -> dict:
        response = await self._make_request(
            "GET",
            f"{self.base_url}/vacancies/{vacancy_id}",
            token=token
        )
        response.raise_for_status()
        return response.json()
    
    async def apply_to_vacancy(
        self, 
        token: str, 
        vacancy_id: str, 
        message: str, 
        resume_id: str = None
    ) -> dict:
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

        response = await self._make_request(
            "POST",
            f"{self.base_url}/negotiations", 
            token=token,
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
        response = await self._make_request(
            "GET",
            f"{self.base_url}/saved_searches/vacancies",
            token=token,
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
        # Parse the URL to extract the path and query parameters
        from urllib.parse import urlparse, parse_qs
        
        parsed = urlparse(search_url)
        
        # Make sure we're using the API URL, not the web interface URL
        api_url = search_url
        if "hh.ru/search/vacancy" in search_url:
            # Convert web URL to API URL if needed
            api_url = search_url.replace("hh.ru/search/vacancy", "api.hh.ru/vacancies")
        
        response = await self._make_request("GET", api_url, token=token)
        
        if response.status_code != 200:
            logger.error(f"Search by URL failed: {response.status_code}")
            response.raise_for_status()
        
        result = response.json()
        logger.info(f"Found {result.get('found', 0)} vacancies using saved search URL")
        return result