var fontsArr = ["Abadi MT Condensed Light",
"Albertus Extra Bold",
"Albertus Medium  ",
"Antique Olive ",
"Arial ",
"Arial Black ",
"Arial MT ",
"Arial Narrow ",
"Bazooka ",
"Book Antiqua ",
"Bookman Old Style ",
"Boulder ",
"Calisto MT ",
"Calligrapher ",
"Century Gothic ",
"Century Schoolbook ",
"Cezanne ",
"CG Omega ",
"CG Times ",
"Charlesworth ",
"Chaucer ",
"Clarendon Condensed ",
"Comic Sans MS ",
"Copperplate Gothic Bold ",
"Copperplate Gothic Light ",
"Cornerstone ",
"Coronet ",
"Courier ",
"Courier New ",
"Cuckoo ",
"Dauphin ",
"Denmark ",
"Fransiscan ",
"Garamond ",
"Geneva ",
"Haettenschweiler ",
"Heather ",
"Helvetica ",
"Herald ",
"Impact ",
"Jester ",
"Letter Gothic ",
"Lithograph ",
"Lithograph Light ",
"Long Island ",
"Lucida Console ",
"Lucida Handwriting ",
"Lucida Sans ",
"Lucida Sans Unicode ",
"Marigold ",
"Market ",
"Matisse ITC ",
"MS LineDraw ",
"News GothicMT ",
"OCR A Extended ",
"Old Century ",
"Pegasus ",
"Pickwick ",
"Poster ",
"Pythagoras ",
"Sceptre ",
"Sherwood ",
"Signboard ",
"Socket ",
"Steamer ",
"Storybook ",
"Subway ",
"Tahoma ",
"Technical ",
"Teletype ",
"Tempus Sans ITC ",
"Times ",
"Times New Roman ",
"Times New Roman PS ",
"Trebuchet MS ",
"Tristan ",
"Tubular ",
"Unicorn ",
"Univers ",
"Univers Condensed ",
"Vagabond ",
"Verdana ",
"Westminster",
"Allegro ",
"Amazone BT ",
"AmerType Md BT ",
"Arrus BT ",
"Aurora Cn BT ",
"AvantGarde Bk BT ",
"AvantGarde Md BT ",
"BankGothic Md BT ",
"Benguiat Bk BT ",
"BernhardFashion BT ",
"BernhardMod BT ",
"BinnerD ",
"Bremen Bd BT ",
"CaslonOpnface BT ",
"Charter Bd BT ",
"Charter BT ",
"ChelthmITC Bk BT ",
"CloisterBlack BT ",
"CopperplGoth Bd BT ",
"English 111 Vivace BT ",
"EngraversGothic BT ",
"Exotc350 Bd BT ",
"Freefrm721 Blk BT ",
"FrnkGothITC Bk BT ",
"Futura Bk BT ",
"Futura Lt BT ",
"Futura Md BT ",
"Futura ZBlk BT ",
"FuturaBlack BT ",
"Galliard BT ",
"Geometr231 BT ",
"Geometr231 Hv BT ",
"Geometr231 Lt BT ",
"GeoSlab 703 Lt BT ",
"GeoSlab 703 XBd BT ",
"GoudyHandtooled BT ",
"GoudyOLSt BT ",
"Humanst521 BT ",
"Humanst 521 Cn BT ",
"Humanst521 Lt BT ",
"Incised901 Bd BT ",
"Incised901 BT ",
"Incised901 Lt BT ",
"Informal011 BT ",
"Kabel Bk BT ",
"Kabel Ult BT ",
"Kaufmann Bd BT ",
"Kaufmann BT ",
"Korinna BT ",
"Lydian BT ",
"Monotype Corsiva ",
"NewsGoth BT ",
"Onyx BT ",
"OzHandicraft BT ",
"PosterBodoni BT ",
"PTBarnum BT ",
"Ribbon131 Bd BT ",
"Serifa BT ",
"Serifa Th BT ",
"ShelleyVolante BT ",
"Souvenir Lt BT ",
"Staccato222 BT ",
"Swis721 BlkEx BT ",
"Swiss911 XCm BT ",
"TypoUpright BT ",
"ZapfEllipt BT ",
"ZapfHumnst BT ",
"ZapfHumnst Dm BT ",
"Zurich BlkEx BT ",
"Zurich Ex BT"];

(function (document) {
        var width;
        var body = document.body;
      
        var container = document.createElement('span');
        container.innerHTML = Array(100).join('wi');
        container.style.cssText = [
          'position:absolute',
          'width:auto',
          'font-size:128px',
          'left:-99999px'
        ].join(' !important;');
      
        var getWidth = function (fontFamily) {
          container.style.fontFamily = fontFamily;
      
          body.appendChild(container);
          width = container.clientWidth;
          body.removeChild(container);
      
          return width;
        };
      
        // Pre compute the widths of monospace, serif & sans-serif
        // to improve performance.
        var monoWidth  = getWidth('monospace');
        var serifWidth = getWidth('serif');
        var sansWidth  = getWidth('sans-serif');
      
        window.isFontAvailable = function (font) {
          return monoWidth !== getWidth(font + ',monospace') ||
            sansWidth !== getWidth(font + ',sans-serif') ||
            serifWidth !== getWidth(font + ',serif');
        };
      })(document);

function getFontsInstalled() {
        var myMap = new Object();
        for (var i = 0; i < fontsArr.length; i++) {
                myMap[fontsArr[i]] = isFontAvailable(fontsArr[i]);
        }
        jsonStr = JSON.stringify(myMap)
        return jsonStr;
}
function getBrowser() {
	var userAgent = navigator.userAgent;
	var brwoser = '';

	if (userAgent.indexOf('Opera') != -1) {
	     browser = 'Opera';
    }
    else if (userAgent.indexOf('OPR') != -1) {
        browser = 'Opera';
    }
    else if ((verOffset = userAgent.indexOf('Edge')) != -1) {
        browser = 'Microsoft Edge';
    }
    else if (verOffset = userAgent.indexOf('MSIE') != -1) {
            browser = 'Microsoft Internet Explorer';
    }
    else if (verOffset = userAgent.indexOf('Chrome') != -1) {
            browser = 'Chrome';
    }
    else if (verOffset = userAgent.indexOf('Safari') != -1) {
            browser = 'Safari';
    }
    else if (verOffset = userAgent.indexOf('Firefox') != -1) {
            browser = 'Firefox';
    }
    else if (userAgent.indexOf('Trident/') != -1) {
            browser = 'Microsoft Internet Explorer';
    }
	return browser;
	}

	function getOS() {
	var clientStrings = [
            {s:'Windows 10', r:/(Windows 10.0|Windows NT 10.0)/},
            {s:'Windows 8.1', r:/(Windows 8.1|Windows NT 6.3)/},
            {s:'Windows 8', r:/(Windows 8|Windows NT 6.2)/},
            {s:'Windows 7', r:/(Windows 7|Windows NT 6.1)/},
            {s:'Windows Vista', r:/Windows NT 6.0/},
            {s:'Windows Server 2003', r:/Windows NT 5.2/},
            {s:'Windows XP', r:/(Windows NT 5.1|Windows XP)/},
            {s:'Windows 2000', r:/(Windows NT 5.0|Windows 2000)/},
            {s:'Windows ME', r:/(Win 9x 4.90|Windows ME)/},
            {s:'Windows 98', r:/(Windows 98|Win98)/},
            {s:'Windows 95', r:/(Windows 95|Win95|Windows_95)/},
            {s:'Windows NT 4.0', r:/(Windows NT 4.0|WinNT4.0|WinNT|Windows NT)/},
            {s:'Windows CE', r:/Windows CE/},
            {s:'Windows 3.11', r:/Win16/},
            {s:'Android', r:/Android/},
            {s:'Open BSD', r:/OpenBSD/},
            {s:'Sun OS', r:/SunOS/},
            {s:'Linux', r:/(Linux|X11)/},
            {s:'iOS', r:/(iPhone|iPad|iPod)/},
            {s:'Mac OS X', r:/Mac OS X/},
            {s:'Mac OS', r:/(MacPPC|MacIntel|Mac_PowerPC|Macintosh)/},
            {s:'QNX', r:/QNX/},
            {s:'UNIX', r:/UNIX/},
            {s:'BeOS', r:/BeOS/},
            {s:'OS/2', r:/OS\/2/},
            {s:'Search Bot', r:/(nuhk|Googlebot|Yammybot|Openbot|Slurp|MSNBot|Ask Jeeves\/Teoma|ia_archiver)/}
        ];

	for (var id in clientStrings) {
        var cs = clientStrings[id];
        if (cs.r.test(navigator.userAgent)) {
            return cs.s;
        }
	}
	return '';
	}

	function getDeviceInfo() {
	var xmlHttp = new XMLHttpRequest();
	var infoURL = window.location.protocol + "//ipinfo.io/json"
    xmlHttp.open("GET", infoURL, false);
    xmlHttp.send(null);
	locationResponse = JSON.parse(xmlHttp.responseText);

	// Create JSON object for the device
	var deviceInfo = new Object();
	deviceInfo.loc = locationResponse.loc;
	deviceInfo.browser = getBrowser();
	deviceInfo.os = getOS();
	var deviceJSON = encodeURIComponent(JSON.stringify(deviceInfo));
	return deviceJSON;
    }