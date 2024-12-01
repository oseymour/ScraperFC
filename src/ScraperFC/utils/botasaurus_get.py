from botasaurus.request import request, Request
from botasaurus_requests.response import Response

@request(output=None, create_error_logs=False)
def botasaurus_get(req: Request, url: str) -> Response:
    """ General purpose "get" function that uses Botasaurus.
    
    Parameters
    ----------
    req : botasaurus.request.Request
        The request object provided by the botasaurus decorator
    url : str
        The URL to request
        
    Returns
    -------
    botasaurus_requests.response.Response
        The response from the request
    """
    if not isinstance(url, str):
        raise TypeError('`url` must be a string.')
    resp = req.get(url)
    return resp