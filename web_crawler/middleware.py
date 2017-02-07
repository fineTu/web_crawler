import gtk
import jswebkit
import logging
from scrapy.http import HtmlResponse
import webkit


class WebkitDownloader( object ):

    def stop_gtk(self, v, f):
        gtk.main_quit()

    def _get_webview(self):
        webview = webkit.WebView()
        props = webview.get_settings()
        props.set_property('enable-java-applet', False)
        props.set_property('enable-plugins', False)
        props.set_property('enable-page-cache', False)
        return webview

    def process_request( self, request, spider ):
        if 'renderjs' in request.meta:
            webview = self._get_webview()
            webview.connect('load-finished', self.stop_gtk)
            webview.load_uri(request.url)
            gtk.main()
            ctx = jswebkit.JSContext(webview.get_main_frame().get_global_context())
            url = ctx.EvaluateScript('window.location.href')
            html = ctx.EvaluateScript('document.documentElement.innerHTML')
            return HtmlResponse(url, encoding='utf-8', body=html.encode('utf-8'))
        
        
class SpiderExceptionHandler(object):    
    @classmethod
    def from_crawler(cls, crawler):
        return cls()
    
    def __init__(self):
        print "init SpiderExceptionHandler!!!!!!!!!"
        self.logger = logging.getLogger("SpiderExceptionHandler")
        
    def process_spider_exception(self, response, exception, spider):
        print "handler in !!!!!!!!"
        self.logger.info("response:%s",response)
        self.logger.info("exception in spider:%s ,exception:%s",str(spider.name),str(exception))
        return []
        
        
        