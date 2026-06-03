// ============================================================
//  GLOBAL ELECTRONICS — Catálogo de Precios en Vivo
//  Deploy: Implementar > App web > Ejecutar como: Yo > Cualquier persona
// ============================================================

var SPREADSHEET_ID = '1hoE3vl1EzHy8VBdU82MeE-oc9pcwrfiStAe678F4R5o';
var BANNER_FILE_ID  = '1J81QzHmeh6esiGHcZ3FIbG0u7bGeAMjT';
var LOGO_FILE_ID    = '1RNGyq8BzBzuo9KbDkelo8XgxcwYVVxn5';

// ---------------------------------------------------------------
// Logo — lo busca en Drive al momento de renderizar el servidor,
// lo convierte a base64 y lo cachea 1 hora.
// ---------------------------------------------------------------

function getLogoDataUrl() {
  try {
    var cache = CacheService.getScriptCache();
    var cached = cache.get('global_logo_b64');
    if (cached) return cached;
    var resp = UrlFetchApp.fetch(
      'https://drive.google.com/thumbnail?id=' + LOGO_FILE_ID + '&sz=w220',
      {headers: {Authorization: 'Bearer ' + ScriptApp.getOAuthToken()}, muteHttpExceptions: true}
    );
    if (resp.getResponseCode() !== 200) return '';
    var ct = resp.getBlob().getContentType() || 'image/png';
    var dataUrl = 'data:' + ct + ';base64,' + Utilities.base64Encode(resp.getBlob().getBytes());
    cache.put('global_logo_b64', dataUrl, 3600);
    return dataUrl;
  } catch(e) {
    return '';
  }
}

// ---------------------------------------------------------------
// SKU → Drive file ID map (288 imágenes desde CATEGORÍAS MATIAS PM)
// ---------------------------------------------------------------

var SKU_IMAGES = {
  'ASPIROBOTAT900-SED-BL': '1EeNH9aYwhsp-KuuTvQWXVNoZpF4QlIc7',
  'ASPIROBOTV6SPRO-BK': '1eop-W8crxOBtQqQ-4PTo95GAM-StxS-c',
  'AUTOR-75G-A4': '10VsM_laR8dA8Of2qR2h3lpCsl-2KXC8O',
  'AUTOR-80G-A4': '1_5qX8SSYadlYTugeBbjrmWHulB9lUszp',
  'AUTOR-80G-OF': '1b-U41uSRXg6D9LooGfYkCaIDT3JXJUQ7',
  'BOTSUB-ALU-2TOPS-500ML-W': '1x8t9HTO6_DqpIDEFxDJbp_wd3E83V73_',
  'BOTSUB-ALU-PORTLID-500ML-W': '1MuTzJ44-RAx1BiVeUZigwknQuKIY3eOD',
  'BOTSUB-ALU-SPORTCAP-500ML-W': '1q_shlwsfgMPOSb2GUZ1720IGFeEq_JJy',
  'CABEZALREP-CIZALLA-A4-5EN1': '1fztckKYu3dqZn4rOFt5GvJpcpbMbpVIE',
  'CHOPPSUB-GLS-FROST-16OZ': '1OvAfuIjtiGEI8U6Ps0_KtCi0D4QAkAIp',
  'CINTACORTE-UCN015-50M': '1moWbIswG_GYaTuEoI6Xz5R-_8mn5kunc',
  'CINTACORTE-UCN015-5M': '1p4pIIWDMhdodKb3hrvERA5CqMw6R24jV',
  'CIZALLA-130CM': '1IOSVAzhOiFMobw-vKq1PaG2M67LnNl_N',
  'CIZALLA-A4-12EN1': '1Wk96l4LxNnDjYd6pZ4czlXNC01Y0QkzN',
  'COFMUGSUB-DTEMP-500ML-W': '1CX7PCWNeJkyalrr1g_hJHkvtgQTS2O0V',
  'CRAFTKNIFE': '1cIf2WCFidBxgFaPQRRMgBLhDHMdJJjA4',
  'CUTMAT-A1-B': '1InTOjewn9kjvSUlof8qQ8BpvZG6inDmi',
  'CUTMAT-A1-G': '1raGFfImpS88ePCaLo2OTso7xY5FVugxG',
  'CUTMAT-A1-P': '1_UNrBHJnqSQ7qjAgk9O4w0radSqN30L_',
  'CUTMAT-A1-V': '1TofZDMcw8KjR9St2YiDzAre5UsbeqAhP',
  'CUTMAT-A2-B': '1xKdbZDgIqddSwAeVQKQtyIAARkNyzEtw',
  'CUTMAT-A2-G': '1_6GUu5N4gfSBRUuTsqHB0cqM-hiAZdd6',
  'CUTMAT-A2-P': '1o0nd1LEIjgc8z8Zs2wE5l1WT1u-UKIHO',
  'CUTMAT-A2-V': '1TT32oBalJT8gpRtK_BtCzus1BKRQzsT-',
  'CUTMAT-A3-B': '1dEaHED25oHWwDOmgccESE3pPcAv760Sb',
  'CUTMAT-A3-G': '1tH2nO6gB7A-I4-kG_9hNUSpq2Yjry8Ti',
  'CUTMAT-A3-P': '1gYwEpq8F5_jpr7e0hl4Ooyaze4hiBQ-q',
  'CUTMAT-A3-V': '1rw122wP3AUtV_8LnEmXAYgN3FcVMtAk5',
  'CUTMAT-A4-B': '1qxQOp3BU-nTm2HtS6Q3IIl-gTMApQxNA',
  'CUTMAT-A4-G': '19ZJ_G68gG_KSAmkBx7PJ7y5_nPSGBwnb',
  'CUTMAT-A4-P': '1Efb_lULVr986IYWmGiF8RxUlH8vdBPNH',
  'CUTMAT-A4-V': '1qAsjWu1Fw9ifCBXuO2kKMcRY_WgaxKz1',
  'CUTTER-CN051': '1sUJKaWJ2GcsY5dWfjIQbVp49CHQ4qS5H',
  'CUTTER-UCN001': '1KIh6ZDb5XU7r6pWNBAZ5N62fsr7e4tRG',
  'CUTTER-UCN003N': '1t_IZImjCjdcvpickza9VL3AkUBIHSIwN',
  'CUTTERCIRCLE': '1ObJiS401s9oO4U4gWvj15hCDWmTaKY4G',
  'CUTTERROTA-45MM': '1YkisHQ72L8Twon3A7z7I8lQVjdF3Eg8u',
  'DOBLEWIRE-2:1-M-A4': '1NDjE6nlIVkicnPpqhq6Zdw4UxsoeNckG',
  'DUPLITUC-70G-A4': '1Iu-tTiC4K1rQXbXBTesfCgj-wh7eZmeb',
  'EMERLIGHT-30LED': '1pkNtTeC_eisIPOjfBTcfCZkbFR-lUrPT',
  'EMERLIGHT-60LED': '1L05rizpscYMFpbUme4IzPU2dXH7mgnji',
  'ESPATULA-SET-UA150': '1D9ltoRJ7QDrfdgJSZmH4lDKReP1WX3Q-',
  'ESPATULA-SET-UA97': '1dQwy_VSCL4jlYSY2dVySFnr_RzI6eXDQ',
  'ESPATULA-UA02G': '1N1o7wLf5Efyr6gGcWSP9ZA4T6TL2kNc_',
  'ESPATULA-UA02S': '1JLsgmGrOJuX8CTU-oqGluqIYwUUvkgU3',
  'ESPATULA-UA61': '1pyTW8vrMFNW-25mFJw5XvlJzr8zwAnFV',
  'ESPIRALADORA-M-A4': '1PXlva6u9G7RRh2v0d1EoC9r1-bkJr_r3',
  'ESPIRALADORA-M-A4-2': '1Mtp2giPJrVwXHHYX-E2C3Nb7qBdoZfTx',
  'ESPIRALADORA-M-A4-R': '1KyyZurd30RB3cccBL1Rx6FxBja_HEpn3',
  'EXPANSIONDISC-A4-G': '1nzQkYTfjxB29WL0ULpxRmfXElOSNB_ao',
  'EXPANSIONDISC-A4-P': '1B0ICnKd6M1C2ONIYCBzjyRfPdguGf6o1',
  'EXPDISC-32MM-X11-B': '1hGE0E9r8J-AN2bHrKk6a564DH9Lt2VCN',
  'EXPDISC-32MM-X11-BLK': '1CfyJ74sZiqS5G44cfA8xcGcGC-8Faok2',
  'EXPDISC-32MM-X11-O': '1CHjhgUSIGTV9i8bVoNlKTZqG75FwfNsv',
  'EXPDISC-32MM-X11-R': '1oTD7gI7YOdgUiqXeMT6u4WA_qMFJwQrT',
  'EXPDISC-32MM-X11-W': '1gnFfYc_cZujGuYOnUaAoTvD0JM49UvhL',
  'EXPDISC-CORA-24MM-X11-B': '1OtG6WcFhF51CQ5basHiwyB11-B17qESL',
  'EXPDISC-CORA-24MM-X11-G': '1S0QkG4qotuzpKeK6kIlFAJKiZlWAV3SQ',
  'EXPDISC-CORA-24MM-X11-O': '19fFqobu-lUwb6Y66dLhmJlrfiEU7jHug',
  'EXPDISC-CORA-24MM-X11-P': '1l2SXj7yr9COBzp3uzFnase-6pHniNWtV',
  'EXPDISC-CORA-24MM-X11-PU': '1z25_2A62afbg5mWEzBT8C1JnClBk-3IL',
  'EXPDISC-CORA-24MM-X11-Y': '1cYmu_TBOXsn6KzvXbMslNo4yp9m1Bjtv',
  'FOILBLACK-G-32X6MT': '14JYbOnkpyjwmQ8ySPsoqSadHIOpb-lwF',
  'FOILBLUE-G-32X6MT': '1kvYf-F28YmTyRAwxbFwIfWQyG3w0H635',
  'FOILCOPPER-G-32X6MT': '1VGBeTxAnSQ2ZXx0Es8Gfpte_F09eqtSR',
  'FOILGOLD-G-32X6MT': '1IJDuBJwqoAxK3yBlew2Ur77U66joqtFj',
  'FOILGOLD-M-32X6MT': '1Q1JCrtS4Sr7fnrAjcSLfAj1TtPpRzUHh',
  'FOILGREEN-G-32X6MT': '1Pe8IxOoxJXQMUmJzPRG7BbDJ_p9-rH7G',
  'FOILHOLOBLUERAINBOW-G-32X6MT': '1PI3h3aaOApWRr9d922IMxuCEj53Tegha',
  'FOILHOLOGOLDRAINBOW-G-32X6MT': '10UQbIZjNshtBtsDspb9CTz4lKR2yOBrd',
  'FOILHOLOMULTICOLOR-G-32X6MT': '1C5WS4V44A5w9PFxAdOaBONgAX6_0IGBd',
  'FOILHOLOSILVERRAINBOW-G-32X6MT': '1So2rUzF_0PK7XU006YGoIcdJCfl6SNYu',
  'FOILMINTBLUE-G-32X6MT': '1f0B1zMHj-CpKQEjez_mCBtoga6VMGMNg',
  'FOILPINK-G-32X6MT': '1Dm9Aio1VkQfX3FJBOwNWw1m-qA-AvzHE',
  'FOILPURPLE-G-32X6MT': '17me9n6l7mD8YyHQzI0OuaRzg6Zxz4puM',
  'FOILRED-G-32X6MT': '10ytfO8xZ6vflp--k78vWkgejPMtz6KqJ',
  'FOILROSEGOLD-G-32X6MT': '1dKUMgmhDsbYT5MmXfUcX-6uF2ml6PvY3',
  'FOILROSERED-G-32X6MT': '1mVrFFEa3amlWk01ttuU4kWSbvh5IPtQP',
  'FOILSILVER-G-32X6MT': '1uRlreLyQmTG9A1QwMD_VGk34aWsn7Rx_',
  'FOILSILVER-M-32X6MT': '1mG3hOtUAER4IZvBnT61YVH2ZMXsCh4xe',
  'G720S-BLADES30': '1XHhdpz75tBE7dsDRI7QYqOaGOu9QWhSP',
  'G720S-BLADES45': '1CMnbNE8P7QyQzre5Px0Ej-SZudwBBEAN',
  'G720S-BLADES60': '1s3P0JYOYLlyPM1BijKF93RQri9_XjHCQ',
  'GLOBAL-G430Q3': '1L8Q88oSS-kjmpmNSrZUTkLcB3-bDJ31C',
  'GLOBAL-G430Q3-OUTLET': '1OLKugkVDi5s81Pzeg2Xl3pgVpWh2AYzB',
  'GLOBAL-G720S': '14VL2L9Z48QU38Mfbp-hC1-kP9dpY1gmF',
  'GOMASILICON-SUB-30X38': '1ewpdjmTd33C-bffoQQCWX0wO4RX-sirk',
  'GOMASILICON-SUB-40X60': '1Cme_ZRbyUPCj3SxZHaWhJNHbQYj-LKAZ',
  'GORRATRUCKERSUB-BK': '1AU3-9hGDr1cmyFBUI5nYV5OiWVXYHfHQ',
  'GORRATRUCKERSUB-BL': '1O-NniJxGxvO2GRfZz7AQhUJwo5DBrAqw',
  'GORRATRUCKERSUB-CAM': '1ljAUcA82GDXslK9ClRgbJYVIwUgysqpV',
  'GORRATRUCKERSUB-FBK': '1kfpY1zmDhAApxxqmQaJAIhFQJhgY6FZV',
  'GORRATRUCKERSUB-G': '1R-UrjiSU8PgFLayNnar0-7sP0HkiA9Ko',
  'GORRATRUCKERSUB-LBL': '15gWPyuas1UMFzO5WhM7XnL-UAdK2Gwpk',
  'GORRATRUCKERSUB-LGR': '1_pcZRgG7o-pMrANA4uL4VNQnKSgOs0nx',
  'GORRATRUCKERSUB-O': '1MVdKptvqWVwz2dJM-2JuTbvDaFn_Kjfg',
  'GORRATRUCKERSUB-R': '1bhZWhq5RLvune3J715TJl_tHuq6mnvWW',
  'GORRATRUCKERSUB-W': '17ugfdO_ARInrw-XS6XaFUqZmd7v06HKE',
  'GORRATRUCKERSUB-Y': '1bXX724EUq047J7uRKZ0gwbAPeqrD79Mo',
  'GUILLOTINA-A3-METAL': '15W27LbstxSV4BIpv8DZh6qFijVB4X17M',
  'GUILLOTINA-A4-METAL': '1Uu-MP30QjILYb1lnfyPys6yAF8AYKIQ6',
  'HEATTAPE-10MM': '1_CZjYhwnb2-eIkEAV0ra0Enb_6ZBfykT',
  'HEATTAPE-20MM': '1EUYr2xf7IDlX6PrNY36xRTC0-U8UsXIH',
  'HEATTAPE-6MM': '13iukq52KyDsV4Sb3Gxpw8Dy163gRqxyi',
  'HTV-3DPUFFPU-BLACK-M-50X25MT': '1rpd-x6etf9Qizvpx5tFmBD1oluHMBcHW',
  'HTV-3DPUFFPU-BLACKISHGREEN-M-50X25MT': '12gLW3y5zkO5jguevhmkRgl527OD1hMiI',
  'HTV-3DPUFFPU-BLUE-M-50X25MT': '1suOQcAQEgR_XebCvZaNlE9LMFXbT3LsD',
  'HTV-3DPUFFPU-FLUOGREEN-M-50X25MT': '1qt0i9anQ46-moO8SGv7IR9YPOmI-XrLV',
  'HTV-3DPUFFPU-FLUOPINK-M-50X25MT': '1jDAkmOfpdI0deZ3JR4Wztfm8rpDxDykn',
  'HTV-3DPUFFPU-FLUOYELLOW-M-50X25MT': '1uov9Zu_JgBUPw_KhI5mTdbMrPjQRN4po',
  'HTV-3DPUFFPU-GREY-M-50X25MT': '1bQWqnUnl4Lfl_kv4jSH4X354HdThVuwB',
  'HTV-3DPUFFPU-ORANGE-M-50X25MT': '1Fa47H9vnwWUBTa7ywrNhI0JjLWBz4ZCO',
  'HTV-3DPUFFPU-ORANGERED-M-50X25MT': '1JvI4YsrAW95F_R0i0P27SfyYam2TFD9q',
  'HTV-3DPUFFPU-ORANGEYELLOW-M-50X25MT': '1Uaivh2UTEYXI3dpU-4_zZ24gjTO1Y13k',
  'HTV-3DPUFFPU-PINK-M-50X25MT': '1GPQTjF1f7OIG8BqzlgPbgQq9C3AhQEuJ',
  'HTV-3DPUFFPU-PLUMPURPLE-M-50X25MT': '1LGQziDAbYe5od045rild75wS2bEVLW4e',
  'HTV-3DPUFFPU-RED-M-50X25MT': '1DoM9A8xhXEv5m5H3WWqs0bfhEbpUJBdk',
  'HTV-3DPUFFPU-SKYBLUE-M-50X25MT': '1OE_6nMFO_G6tyNXTR59bTXVrQ2eAiH0-',
  'HTV-3DPUFFPU-WHITE-M-50X25MT': '1UM-DmrVzklyztEuQyUZzb0NsgwSsNp70',
  'HTV-3DPUFFPU-YELLOW-M-50X25MT': '1MbU_alac6XCe_CxKVUmmq3m2Un50PP_p',
  'HTV-FLOCKPU-BLACK-M-50X25MT': '1d84gGqeQReKcHIMDoUgbT2wTVZoy6CUh',
  'HTV-FLOCKPU-BLUE-M-50X25MT': '1qAoCxbEjHc2qr7DcsMdYc4NLfVnj8qjl',
  'HTV-FLOCKPU-BROWN-M-50X25MT': '1EX6XfSCyG8c5V1MO4hkYxxb-w5nVMZdI',
  'HTV-FLOCKPU-DARKGREENGREY-M-50X25MT': '1Ne6NJAtFTXG8-nZRqDjgyUqJY5AQi9L0',
  'HTV-FLOCKPU-DARKGREY-M-50X25MT': '152A54j6jki5to8tRrrYvQ0uVSKi3fksG',
  'HTV-FLOCKPU-DARKGREYRED-M-50X25MT': '1WGzAYP60YVQpaBTEpgjc4bdkmGn99laQ',
  'HTV-FLOCKPU-DARKYELLOW-M-50X25MT': '1_5GT70-L4K2byhuMcsuZW68RjuoeomXb',
  'HTV-FLOCKPU-DEEPPURPLE-M-50X25MT': '1bCwjGyjRkmUD8di9GaeGYr5ogVguIQhh',
  'HTV-FLOCKPU-GRASSGREEN-M-50X25MT': '1WsBt2guRzVz4Gc7IiPBdmRsDRy-p-VZB',
  'HTV-FLOCKPU-GREY-M-50X25MT': '1gKY-lFw0yPWX28soxFOd5GpUA2_7-Us-',
  'HTV-FLOCKPU-MIDDLEBLUE-M-50X25MT': '12SazNV9yE4U4oIozod6lArBIsOjEDSlW',
  'HTV-FLOCKPU-MIDDLEBROWN-M-50X25MT': '1lgkD50xtKDlIz_cKxR0fkJM_QhQtbkPF',
  'HTV-FLOCKPU-NAVY-M-50X25MT': '16Zhq6ytSYGAolAjwJ8yXbEnW5CEmuscP',
  'HTV-FLOCKPU-NEONGREEN-M-50X25MT': '1jdcV1ix0-WyBKKpvIRvOq9XZHU90QspW',
  'HTV-FLOCKPU-NEONORANGE-M-50X25MT': '1fF3j6Ftad_j8-qk4-ct506g_5MCfa7y8',
  'HTV-FLOCKPU-NEONPINK-M-50X25MT': '1_p8xov4jzBIYi_bDp12rRDvvEYoCaAZz',
  'HTV-FLOCKPU-NEONPURPLE-M-50X25MT': '1AvQi4kNTPVqyjgqwB5e5e8PwFKLBZF2d',
  'HTV-FLOCKPU-NEONYELLOW-M-50X25MT': '1oUNtyOpukOhp-rsfVty0ECuVgLAHjX7w',
  'HTV-FLOCKPU-PURPLE-M-50X25MT': '1UI-uKSdPtRFEhWS7BMqUgraMCB8Ua86b',
  'HTV-FLOCKPU-RED-M-50X25MT': '166vSQHhmCIHXe2fbL7lj8Y46QmlDJy3V',
  'HTV-FLOCKPU-SIGNALYELLOW-M-50X25MT': '18E1GN2z8ogB-JR40iy2LvJ9wbXVjaBpt',
  'HTV-FLOCKPU-SKYBLUE-M-50X25MT': '1WsKOpYanHPiSlQEKWn_B5pbmgyFNBqTP',
  'HTV-FLOCKPU-WHITE-M-50X25MT': '1YaKJ995GnDoFByA7yhZXfKjr6o-gPMi8',
  'HTV-FLOCKPU-YELLOW-M-50X25MT': '1OQ0DuEOZ4DC3pk_ux4doQmwj4No1bhyJ',
  'HTV-GLITPU-AQUABLUE-M-50X25MT': '1sFHPAX0Us_-7EIaqHBJRnqEfdzBRw9ac',
  'HTV-GLITPU-BLUE-M-50X25MT': '1qfeGTt9aG7mT-OgXwTfrUJqP-QmEP8qT',
  'HTV-GLITPU-CHERRY-M-50X25MT': '1M5i5FfwDdKPxpkjyILXOrrcZBQaUjvzX',
  'HTV-GLITPU-CONFETI-M-50X25MT': '1E5wayLFj3TxEXAPSKhIUdoGuauWkC1p5',
  'HTV-GLITPU-COOPER-M-50X25MT': '1nivxKzZhW0wKM_-i6yAimj1f_PPmNDci',
  'HTV-GLITPU-DARKGOLD-M-50X25MT': '1gneqfCueG30kH33c3jghB_j8I5EpI1y4',
  'HTV-GLITPU-EMERALD-M-50X25MT': '1j_4uZxMWJBgcmhpQ6vMiAdr7GlgYdJZU',
  'HTV-GLITPU-GALAXYBLACK-M-50X25MT': '18pAkbO88D33fHxyy6qCIAJYRUMn4P49D',
  'HTV-GLITPU-GRASSGREEN-M-50X25MT': '1ZA20yGpcFW1P0rxIcbKQ-MoztVFFOLch',
  'HTV-GLITPU-GREY-M-50X25MT': '1tQk6tVD4uvOuO2Os4I68X7TMPHtn9U1J',
  'HTV-GLITPU-HOTPINK-M-50X25MT': '1f123RNk70UZ_Cp6HW8FErp432Ud-ZB80',
  'HTV-GLITPU-LIGHTGREEN-M-50X25MT': '1zxP48LInjLo-0JYrLA33rHSTW6BtxIkH',
  'HTV-GLITPU-NEONBLUE-M-50X25MT': '1oAoGJZhs3nTXx4av_dnfpxKnUVpq4rb3',
  'HTV-GLITPU-NEONGRAPEFRUIT-M-50X25MT': '12rIrtJF4tqwX7lI6GKQxoVvb3u4v3wj3',
  'HTV-GLITPU-NEONGREEN-M-50X25MT': '1Nbi4jlgF0NNY4KFBbfVH0pgNa4K4XLD9',
  'HTV-GLITPU-NEONPINK-M-50X25MT': '1jBayFM2APHf1pgiFTwSPmOEmObOlJfJ1',
  'HTV-GLITPU-NEONPURPLE-M-50X25MT': '1oZ-uhgYR_GP4fw13MLgVtgj-zsaYTXzb',
  'HTV-GLITPU-NEONYELLOW-M-50X25MT': '1eLKC2EpXYd75K2aY4pUfRTC2NKmBCNbx',
  'HTV-GLITPU-PINK-M-50X25MT': '1iEFj0XJcxAaFLXn4gUMbCL2DU2Hn9O_s',
  'HTV-GLITPU-PURPLE-M-50X25MT': '1eOwup9iCVehbYzk2Lh58FCP7qFljIYLC',
  'HTV-GLITPU-RAINWOBWHITE-M-50X25MT': '1upxnOP2fu5v1Ve0UTAWf6wGczGNRecW_',
  'HTV-GLITPU-RED-M-50X25MT': '14geFYch5vLhT_EBTlkdf2JaULbwa_YvI',
  'HTV-GLITPU-ROYALBLUE-M-50X25MT': '1Jn-CThHx5FVrCOy17_7rh64WDTRoJplV',
  'HTV-GLITPU-SILVER-M-50X25MT': '1Yuf6pYkpufgTB2b1LbbxefOLE6qwazuE',
  'HTV-GLITPU-WHITE-M-50X25MT': '1s_oX9CuI9xO2XOTI4aj-862Zi_bBjiyW',
  'HTV-PU-APPLEGREEN-M-50X25MT': '1N8-Aw6ka9a5LMWtQa8-HagumHm90H6Ws',
  'HTV-PU-AQUAMARINE-M-50X25MT': '1omOtSnQ-fGPTQZSN7TeHWSAbd5pSzsDr',
  'HTV-PU-BEIGE-M-50X25MT': '1CTDGER_MKDmYHfVAQvX3Tu1Dcw0M9ylH',
  'HTV-PU-BLACK-M-50X25MT': '1vGGwGk7F8U3bGFgOK_x-R1y2rLwcPhLj',
  'HTV-PU-BROWN-M-50X25MT': '19yAyRVVjFiEeBtpdt5cZNZBPGA1mdxlo',
  'HTV-PU-CAMUARMYBLUE-M-50X25MT': '1yEppMWeTLV8WskLvx2hzLm5R09f0Jfdt',
  'HTV-PU-CAMUARMYGREEN-M-50X25MT': '1P3vCKWBzMcH9FvvYBhLasqVvhMr5Jz_o',
  'HTV-PU-CAMUARMYRED-M-50X25MT': '1LqRZdgkSN7TQjBm0A6uh517T7dA7CdlH',
  'HTV-PU-CAMUBLACKWHITE-M-50X25MT': '1JNirxsIPtq4-7Klw7mQiHBUrZoghaZQU',
  'HTV-PU-CAMUCOFFEE-M-50X25MT': '1qmL0zoUp30F6AlHSNz86sM1ajTOjP94Z',
  'HTV-PU-CORAL-M-50X25MT': '1CT1IvSTlVBEhOmjp32GIAr7KjPWvfb86',
  'HTV-PU-DARKBLUE-M-50X25MT': '1Y54zSqDUrXtcwLLqzwxSqJjGTi_FKSt-',
  'HTV-PU-DARKGREEN-M-50X25MT': '1K0RMTOHLd6cNjUTYA2wElfGjxqUc4KOq',
  'HTV-PU-DARKGREY-M-50X25MT': '1kVQBNF6swydDTyXMEzqAFDs2aqZQhZpV',
  'HTV-PU-FUCSIA-M-50X25MT': '1k3BR5vrVAhuAWnGnI2o3HFgGoJRCyl8e',
  'HTV-PU-GOLD-M-50X25MT': '1qnuculrq8A0skXOyuPh9J_x8iugRBNQb',
  'HTV-PU-GOLDENYELLOW-M-50X25MT': '1ICY1U0h35xHart7sc2uB7orW9rpBAlOV',
  'HTV-PU-GREEN-M-50X25MT': '1bBPGYn6OE4qdBRiTwlrobsei9F7KMAy7',
  'HTV-PU-GREY-M-50X25MT': '1iMeGYFy862oApfzXOSqbSSRhJzw42L6E',
  'HTV-PU-KHAKI-M-50X25MT': '13u-WUmGTwiUY6YupeDoW98ipo-SE3QAT',
  'HTV-PU-LEMONYELLOW-M-50X25MT': '1zPlbmpnsgJrr_C2bMUB1r8vwiZ-VBvEU',
  'HTV-PU-LEOPARD-M-50X25MT': '1rIR39dDFviykZaLGorgz4lKcIQVf2VpS',
  'HTV-PU-MINTGREEN-M-50X25MT': '1zyID8W9tMQqFtRXGsr82I9fNQCuGMlfD',
  'HTV-PU-NAVY-M-50X25MT': '1J0AgVpbcwVPIggHVHep2yKguoNV8ntOt',
  'HTV-PU-NEONBLUE-M-50X25MT': '13VlQiPoO-bjxORLMub-9bdT4_1vy4kwJ',
  'HTV-PU-NEONGREEN-M-50X25MT': '1dfENq40hMkIgDGmba2q7b3pcALJyTrwI',
  'HTV-PU-NEONORANGE-M-50X25MT': '16MGF4asP1lQR_SqGm3W6OXuRWoFyl8_k',
  'HTV-PU-NEONPINK-M-50X25MT': '1y7Bwkp1Ta8C0D_oDJ8PE5NDhW41oEgAz',
  'HTV-PU-NEONYELLOW-M-50X25MT': '1KHRElwU_iQtZr0w3ipUglkXIx-PASNnX',
  'HTV-PU-OCEANBLUE-M-50X25MT': '1bwC6iU-GwqKUHl2ClJRdZmDk0536iKGO',
  'HTV-PU-ORANGERED-M-50X25MT': '1bkOXw7bdVndwxRjyJkK8IAYmjVTp4tQ8',
  'HTV-PU-PALEBLUE-M-50X25MT': '1B5RRhjDE4BriW-3IX7MYpyKTXiB9Lwzs',
  'HTV-PU-PASIONPINK-M-50X25MT': '1gMELncY2iMni9bJy7rZSe3xXVEJcf7mt',
  'HTV-PU-PASTELBLUE-M-50X25MT': '1Nu3tWjw1s5AL0JZKLtuoPQZNk5QrRIgF',
  'HTV-PU-PASTELGREEN-M-50X25MT': '1ZYZ1TXab9Fdwfs3MuirDME-xhDe9Ovax',
  'HTV-PU-PASTELLIGHTGREEN-M-50X25MT': '13lCP-5C2ND_inXREniN1irMvJcJ1xFXL',
  'HTV-PU-PASTELPINK-M-50X25MT': '13e_9TFN_3Cr6iMQiz0FKyP6dHiU7n3Na',
  'HTV-PU-PASTELPURPLE-M-50X25MT': '1me7Oh-HdudWjehTMFTrRu6g3TvCgbIsf',
  'HTV-PU-PINK-M-50X25MT': '1SgMmdU1HNNCpHOLQmrjRlVSE081tn1E9',
  'HTV-PU-PURPLE-M-50X25MT': '1RxeuJxyU2EbD7OhOyr1uh4Znix-Zc1ks',
  'HTV-PU-PURPLISHRED-M-50X25MT': '12-FMQoncgy8MbkxKKsUFJ098YJhZGxVk',
  'HTV-PU-RED-M-50X25MT': '1DtpHt_nwRgYtkifS7Hx1_9Kuew6Olgs0',
  'HTV-PU-ROSEGOLD-M-50X25MT': '1A4CIu0VaEA9ZFiauVeF7YxXn22GsYmO1',
  'HTV-PU-ROYALBLUE-M-50X25MT': '1iUUKEJf20eQv5_X2wLMNdntKB7Iq4APm',
  'HTV-PU-SIGNALRED-M-50X25MT': '1uQK-7FtOSp6czeJMPVyLUuHOjIdPkOMc',
  'HTV-PU-SILVER-M-50X25MT': '1eXVfkJ7yqlLqsWLa3O6Slsp7hMKx5Pkz',
  'HTV-PU-SKYBLUE-M-50X25MT': '1Yj2GUivDdi46brdkNgIG--EzFRvbLinF',
  'HTV-PU-SNAKECOFFEE-M-50X25MT': '1nXnIduS_epY3rf-c5jfC0N89kLg1hauL',
  'HTV-PU-SNAKEGREY-M-50X25MT': '15dCdbQzcsTJzsdH-vgYvcdCUB3hX5Efa',
  'HTV-PU-SUNYELLOW-M-50X25MT': '1r66VIWrpm9rPmzYkynwWS6Opb6gbQdCh',
  'HTV-PU-WHITE-M-50X25MT': '17B3LGS9MPfe9tvsS8_TW3NDi0yTw-SgP',
  'HTV-PU-YELLOW-M-50X25MT': '1ODN169vyCzNflCw8_L65xDrcxSAYZquc',
  'HTV-PUPRINT-WHITE-M-50X25MT': '10dzv2kJWRY0hPaBFRQPexlZ7CbXMd125',
  'HTV-PVC-ARMYGREEN-G-50X25MT': '11mRH-OYTOttO9tssl2_vww0Agv2nG9za',
  'HTV-PVC-BLACK-G-50X25MT': '1w7cxnI-y_Wt5R3YNV4ShFCTH_ZBOPOEP',
  'HTV-PVC-BLUE-G-50X25MT': '1fYvwjKDNFnCltQ9Lx5rYRqtKMNCZ5JlA',
  'HTV-PVC-CRIMSON-G-50X25MT': '1OO4YIN8qJbBm-eJlUpzIdoG3lCjMe5jn',
  'HTV-PVC-DARKGREY-G-50X25MT': '1zJ8OpgVToffS29snMZvHYpi5RkhvEZf5',
  'HTV-PVC-FLUOGREEN-G-50X25MT': '1Y49O3aAS_EphGPVQXDkrlQVg0xk-BgGC',
  'HTV-PVC-FLUOORANGE-G-50X25MT': '1pH_YHmpS0zOvZWsTccbq7zLc2PQROVGz',
  'HTV-PVC-FLUOPINK-G-50X25MT': '1R42koMSUNnccN9jSFFKhncy75r_dsNXR',
  'HTV-PVC-FLUOYELLOW-G-50X25MT': '1mJbbpcfI6PA0wdn0rR7XGqz0XT92H4IX',
  'HTV-PVC-GOLDEN-G-50X25MT': '1yQS0X0upscUkyoNxR_q15PEtTtkQATVh',
  'HTV-PVC-GRASSGREEN-G-50X25MT': '1x-onmK0jvSh5l7fXbesFYiPBJYGxr3q7',
  'HTV-PVC-GREEN-G-50X25MT': '1wSTdLU5d8BHc54xb-VrPUZrgCLTBzj4u',
  'HTV-PVC-LIGHTBLUE-G-50X25MT': '1Avspe0heV7EH49_Os9HjKvNJmpyUloJ_',
  'HTV-PVC-LIGHTGREY-G-50X25MT': '1g9KixmmR6gJjWNBwweGT-2PKEiAbwgrm',
  'HTV-PVC-LIGHTORANGE-G-50X25MT': '1vCgwTC6oereAOcM5TXcu3vf3fjhp4rjz',
  'HTV-PVC-ORANGE-G-50X25MT': '1ihFbFUUNfQddRtKEiFKOnzZ1o61-t1PZ',
  'HTV-PVC-PINK-G-50X25MT': '1Fj3j4KXwpI_zB8EMbZDQ46QYCj1Sh0Mi',
  'HTV-PVC-PURPLE-G-50X25MT': '1SrOLKEGHdw0Mq7opA0CLRZRdpqPyc_Ol',
  'HTV-PVC-RED-G-50X25MT': '1d_BKoFM_Zw3VWoLGfir7YJO0mlZolF8Z',
  'HTV-PVC-SILVER-G-50X25MT': '1WScUVyK9zgnFNWmxQDi-jPOrBqe-RwJj',
  'HTV-PVC-SKYBLUE-G-50X25MT': '16YUTlgrYsg4N6aO1veHaw34yORyP88fb',
  'HTV-PVC-SOLIDGOLD-G-50X25MT': '1pJvHBZjX9AcczVIERxFsTHNwbp9k8Ukw',
  'HTV-PVC-WHITE-G-50X25MT': '1GWzxWm2FhudbMnYqdcGsV5Ik6E5YmZNq',
  'HTV-PVC-YELLOW-G-50X25MT': '1dmgXGW7IpruExBC_qknDEWrkwWFlS6oi',
  'INKSUBLIC100': '15bwr8oZzz65A0H3kSu-YxKkRaZTEW7zD',
  'INKSUBLIC1000': '1D2R82yGdnuui16kRAwBES7AvYclSy69i',
  'INKSUBLIC250': '1gdmDcjRio3BU-u75ewhHvRMUy-Nmh4hu',
  'INKSUBLIK100': '1We6l3bGyMV8n9LpA13x4fcUqP19sErF4',
  'INKSUBLIK1000': '1FzHzQJOBfx-QbcUPhx7k91GLMnBc0pma',
  'INKSUBLIK250': '1ijMmYR7y7P8nu0hcnUFeNNFwL4EdvFrq',
  'INKSUBLILC100': '19mGXmiK_FqRt6DXWeL_nKjLUoyhgQi6T',
  'INKSUBLILM100': '1fdL-pbtkjGaIGepV5kPQ19EQTbNOCuyc',
  'INKSUBLIM100': '1pAAJcbuf6N7z5Nt0dyWcfHedGjklzbkY',
  'INKSUBLIM1000': '1Bv3LPaX1u24lMRpkSo8i-_YKKqNn679V',
  'INKSUBLIM250': '1q4jmYRIzf_aEAgbrCNbfVrRv7hJyNkL7',
  'INKSUBLIY100': '1p1H9YkSM1ERIMCzPZZBk6PEw2QkcKgHv',
  'INKSUBLIY1000': '1llYlkRR6KEHPLK2Igtrsozd7u0bauHmY',
  'INKSUBLIY250': '19GWOuFZwCH6w2o1LyQQhdFM1fXeFxbht',
  'JS10000-3IN1-AIRP-SC-USBC': '1J5QZRUb9MbQbWTVH0Nq_j9JBMvO2gZ1Z',
  'JS10000-SC-USBC': '1ptfe0vJiU8Gn6sLZ8suwzp1z9VH_jmEJ',
  'JS8000-SC-220V': '1cBsVUy_BueNGNDCjfcEZ9NCyVrjZWmWy',
  'JS8000-SC-USBC': '1_IyMtUTT7-Dzzg5dVGTAsosD-mnUY7PB',
  'LAM-POUCH-G-225X303MM-125MIC': '1QbaxL4HcgWksHKFDwthIkmLfZQvA8bMv',
  'LAM-POUCH-G-225X303MM-150MIC': '1DWiLWvWr8bJs5bNRShjgPYoE6Y5uUiKf',
  'LAM-POUCH-G-225X303MM-80MIC': '1xf9UTbdDNdXKbDsYMZARALh1w55JnLFJ',
  'LAM-POUCH-G-303X426MM-125MIC': '15aqsDv_Sqi8Y66ok8dnewztuXm4ZoZjD',
  'LAM-POUCH-G-303X426MM-150MIC': '1c3SdRlxDOkFveGJXo1U6GVg-Ze-BiDOF',
  'LAM-POUCH-G-303X426MM-80MIC': '1ydiG50Xasa5SnPDXgW-Z7XI3cXDU-s_-',
  'LAM-POUCH-G-60X90MM-150MIC': '1gBv_jcG66P1VqbqM3eIpDdtiOPychxU-',
  'LAM-POUCH-G-67X98MM-150MIC': '1FA1Xl_VWRmmVPITIG401YWlPaMch_4fa',
  'LAM-POUCH-G-90X130MM-150MIC': '1slnnVnsXtwTzyx0XkQfZdH5cUk2kYcNc',
  'LAM-ROLL-G-330MM-150MTS-25MIC': '19ET7xkSwMNBWOX6p-DKaxFZ2_ywSBnN-',
  'LAM-ROLL-G-330MM-150MTS-28MIC': '1peyK1Ip-DnPwcT2BopNE71K1m1yIdI4X',
  'LAM-ROLL-G-330MM-150MTS-32MIC': '1uOtxfDmZM6YMCuY7j3b8kDjzz3PmClEZ',
  'LAM-ROLL-M-330MM-150MTS-25MIC': '1PrDsne68RIWn8GOut1XzGSAN20KG50lK',
  'LAM-ROLL-M-330MM-150MTS-28MIC': '1EJXyqfOLdRuVFVZYnZukko5rmS_suiYq',
  'LAM-ROLL-M-330MM-150MTS-32MIC': '1c_c_nYTcOvJ8YyD20UlfD38jFBtHgDMH',
  'LAMINATOR-230MM': '13zjW29z19l5TCkne65to35Gm0ZivamLX',
  'LAMINATOR-230MM-V2': '13VoqIZ-aIlVrJcQwyC_0FByOxQTsyoD7',
  'LAMINATOR-240MM': '1Is-kb1lJgKYYkpyaOdJbyt0gPgc7sBDN',
  'LAMINATOR-240MM-V2': '1h1rQhby4lNFBarm4Yu-1sVmYSsW8PL3d',
  'LAMINATOR-330MM': '1bVlDWaw9Ie3vJpKowv2QhOfKyVFg-9_H',
  'LAMINATOR-330MM-PRO': '1b17S27vMbLTOt0BVKXFzd7BmmMDSqpsO',
  'LAMINATOR-330MM-V2': '1r6k79iTajZVX1DeELIo1hNI1Eptw5OpL',
  'LEDESMA-NAT-75G-A4': '1LIrDLpFLK_j-BOH5Cl5VRpQD2rwPJoZV',
  'LLAVSUB-MTL-DESTAPADOR': '1eQWPKDLSKmwwNF_KvBNZM3ACHmNlICXf',
  'LLAVSUB-PL-CAMISETA': '1U0ohqa4xulreuh_pfJzVQuJnby7PDDTI',
  'MATESUB-MSTRAW-W': '1DeKkskTE793-g5JB-vBCwjLRs7JLJYYc',
  'MPADSUB-ROUND-20': '13IgFurXjd_VNRG2Fss6VZoryJEjKiGsY',
  'MPADSUB-SQUARE-20X20': '1JMjhK0KJbSMylSN2RLz_a9Dw9zLSPbYC',
  'PAPERAARTWLEATHER160A3-100': '12DEw3gHUWMwXTUZ9iz2OkeHr_Z-AOoAo',
  'PAPERAARTWLEATHER160A4-100': '1E-ph3Y2dVPg8TQzk68T6_s0eOQ3E27ym',
  'PAPERAARTWLEATHER160A4-20': '19jQp-tGut7oLJ2yFXJN7riL1KcJVcF8c',
  'PAPERAG115A4-20': '11H3g8ACmQcClcQ6Eg2QLDrzAKP2yDLHJ',
  'PAPERAG135A3-20': '1mBgHQ3edUz40K_tOKJNKQeCO0XP2yafc',
  'PAPERAG135A4-20': '18CJUV6jDd3VFNbGhQ77O3YvDK3ZZU4aW',
  'PAPERAHOLODROPSA4-100': '1oXBQ3jPX4IICuPBLci-fqMe9zvheswpP',
  'PAPERAHOLODSNOWA4-100': '16t28wtc9FweUbXXEFkjd0XYZymBS2-bB',
  'PAPERAHOLOLOVEA4-100': '13szaeOvzp_3HtuIVjY3RKlJWl6SZxp6_',
  'PAPERAHOLOMIXA4-18': '1_IUapx8T3NrqVFz5jQRerM8XmnhzK7P1',
  'PAPERAHOLOSNAKEA4-100': '1-xJCWp2K3ZPpMBM99Gdz4R9qk3cdxZ2r',
  'PAPERAHOLOSQUAREA4-100': '17wHPJOFNxVCSkrq3DWwu2MA3V5K9LFgS',
  'PAPERAHOLOWAVEA4-100': '11QnYp-kZTO0lb7nrL0o_zYwpqxXnngBp',
  'PAPERAKRAFT180A3-100': '1hYopl_jwXmuK74w7B5_h4PTjWaCYCdlj',
  'PAPERAKRAFT180A4-100': '1K1bt_iatAwL19lVwd93Yh48zR0872NUL',
  'PAPERAKRAFT180A4-20': '1CsxR40bfRSEHXw-dbH1I9MZcEBQOwGuV',
  'PAPERAM108A4-20': '1m-57ktrzI5MWxRASjEZ6a9MMa3doduXC',
  'PAPERATRANSPETRC120A3-10': '16oCVRKTAEWNlfzKajVcm-j0NRfw2HoRI',
  'PAPERATRANSPETRC120A4-10': '14t_DGRSWqhEXPzcC39h4oMjdQjCV1BYJ',
  'PAPERATRANSPP160A4-100': '1RCm3YSBqEX7C4VJ9XtytE80RQNUAOspn',
  'PAPERATRANSPP160A4-20': '1W9ZBwe0NS5NBIup_3DtaUbahTNXWKEcl',
  'PAPERAWPETRC120A4-100': '14IrEpyHMzn3JkoU-OjZ0skcitnjsib6Q',
  'PAPERAWPETRC120A4-20': '1gPn3JSFocTt6FTAORvGcvo9TJjINealb',
  'PAPERDFG180A4-20': '19wfAOx9jimU2vQGtJ1WF_3Jz2uU6i90v',
  'PAPERDFG220A4-20': '1Ml2rMdWNtbm9zePcr5PP3G2Z79AHW6eu',
  'PAPERDFM220A4-20': '1uXTDzJnxUeZs1jLiGf13f_DZS6L1OWas',
  'PAPERG140A4-20': '1_dfU09qZNlDFV9flBHn0ch4lhKHktxlM',
  'PAPERG180A4-20': '1o6ZF5My8w_1_xqU_1rHISABQlv3faCUS',
  'PAPERG180LGL-20': '1hqcnJHt4NSi4DfKCHfiEp7lXObq8xc0B',
  'PAPERG20010X15-20': '1fwW2lzZsAKHsvws3rPoXppwdfCkUuFfR',
  'PAPERG20013X18-100': '1NmkV_dGEKqx2cOaHEX4slHB2piPPVcwP',
  'PAPERG20013X18-20': '1ugDTQbZbE_LlHYSiKT5M-w3kETH6h7aD',
  'PAPERG20015X20-20': '19hxD_BvDDEOHbXxDoPolYKC4uft36cCM',
  'PAPERG200A3-20': '1tM0y2gpe77Q7ScKPO3EQ2-pzBGQM086z',
  'PAPERG200A4-20': '13Rm_17QQ_QSROfyZcStuNeIvbz4Oqs_J',
  'PAPERG260A4-20': '1eVpo4IgI8SZesFCmQU2GQsdwFQYx9cic',
  'PAPERKRAFT125A4-20': '1hOZQdzVJZYlqxE4icwPc9eiZLTiTtBrH',
  'PAPERKRAFT200A4-20': '1-XHOQwgqJwNpISILz0T4sy-CI4hQKkHi',
  'PAPERLUSTER260A4-50': '1EFbRWrMp8JiD3w3zarF86GCTaqg4dkwM',
  'PAPERM110A3-20': '16gaTuInM9sf_xTjKAs2PvjHOQyNCE_vn',
  'PAPERM110A4-100': '1XdSVZ0V_wBdeDW_LI_eEcusDcuXNtzgu',
  'PAPERM110LGL-20': '1mzEKrwd94mrg7lFIOB4lz9GSrUipTHYl',
  'PAPERM150A4-100': '1SsBmrVrMNxGsgiAcA8PT7ZTdA8fGN5hQ',
  'PAPERM150A4-20': '1BXR_4yrDqflqVarSP0RuAVJhMGYs3nQ4',
  'PAPERM180A3-100': '1PR6p-K0kOy9_HN1bNb9JpAu08A2_9tzA',
  'PAPERM180A4-20': '1P84lAFHSvn_nQ-_F8U7tLUEoj9g0GPE6',
  'PAPERM19010X15-20': '1PCe9w9aq4Y_SVZguAu6ELsa6K1ormkta',
  'PAPERM19013X18-20': '1QqKocbcIlZR8WuHyCKTCkEhFbReXjWNM',
  'PAPERM210A4-100': '14z9qsYrblfp1S7U_k2Hk4g5lD8j2qrSq',
  'PAPERM210A4-20': '1e-BGXCzfKglrxwPnRQl5DKrwRUq5LBBA',
  'PAPERM240A3-100': '1qs_NioJvvyqx_oQiE0x5w3QOnbzL6h42',
  'PAPERM240A4-100': '13mmBTo-FgSwwuSGwMX4gunQbov_te6PW',
  'PAPERM240A4-20': '1YV4Zs7d480Rto4G_fiE9OwacfkVowOaD',
  'PAPERMAGNETIC640A4-10': '1w0MjlUbagdNPii7PEDHOjhk45I_d5Xj9',
  'PAPERMCYAN180A4-100': '1GX-9EhEvlwpk4--JZUWAGMjlxch775XW',
  'PAPERMCYAN240A4-100': '1MxV9duitXsmJx6aZQaRxULE7ifA0pFWc',
  'PAPERMGREEN180A4-100': '1FT5mmUBnE0Dopf3HmJm3DSx7NmMkvN4C',
  'PAPERMGREEN240A4-100': '1cZyJEYlffuIrU-qr9CWTTorHHIF1c1nf',
  'PAPERMOPALINAMIX240A4-100': '13CFVurri0s9C2YnvClPZaTWxGplw7sn-',
  'PAPERMPINK180A4-100': '1eWTUMMAt7p90_bpaqZxaGav45u0oDpsn',
  'PAPERMPINK240A4-100': '1E5Sf1Fy780v0zlKjq3aPNiwkP0vD_Yt2',
  'PAPERMYELLOW180A4-100': '1FBtWkwogxO7ToDjqPLP-A2D-2kbUmOEp',
  'PAPERMYELLOW240A4-100': '1qj2RiL7o5uhKmJT8CYxsuKhw-sAocLKh',
  'PAPERSUBLI100A3-20': '1J_mjSLTuF8wk9NNsOBSOOjVcRU1K9s8S',
  'PAPERSUBLI100A4-100': '1S9dZE4EhMuozga0fs5Ja60ULE8VDNafY',
  'PAPERSUBLI100A4-20': '12hz3Af1ta1PUBjfux1Ypi24Cm-XM95YF',
  'PAPERSUBLI100ROLL-1100X50M': '1yKR3CV6UnkZGaNYXP0ywOOpLflj8bCl3',
  'PAPERSUBLI100ROLL-1340X50M': '16wsBYuWwVShPhzrjbCTa7cAgOy8WlHEq',
  'PAPERSUBLI100ROLL-210X100M': '1VZp_w4Ya1z4yuVBzIaMYwl54yFPqIrl8',
  'PAPERSUBLI100ROLL-330X100M': '1ZkTflPP-kt-beu1AAEcxUxUdexpetpTK',
  'PAPERSUBLI100ROLL-610X50M': '1roky0Ocf_w6-ppilzkrCjYAlNzA1RIUX',
  'PAPERSUBLI45ROLL-1620X300M': '1TQPj-VmH9v-ILA6LfyqY59dFrbxI6iuv',
  'PAPERSUBLI57ROLL-1620X300M': '19j0CRjz2W044jvdwJEgib_8W7h_baEOo',
  'PAPERSUBLI73ROLL-1620X200M': '1S-ntiEKI7g2w35houYD0znGvqT-WBm2w',
  'PAPERSUBLI90ROLL-1110X100M': '1zqW1K75-BIiwp_VeG416Vp8g9SdR6aSR',
  'PAPERSUBLI90ROLL-1620X100M': '1syYEECTmEG7h8_Lx28bQh8jU95f8l2em',
  'PAPERTATTOOA4-10': '1wYYihTi__xeQUIPZyweT29-k8GuctN4h',
  'PLANCHA-SUB-26X26-PORT': '1ouWujqaAHpMe_YxBAIQPRA_77DW94Y4K',
  'PLANCHA-SUB-30X38': '1lNvQMhhONKdlvhX038vSk_72UMYjbKfe',
  'PLANCHA-SUB-30X38-10EN1': '1TmL3nHL2rP9XRGJ6E_u6wXSMqU-5sAci',
  'PLANCHA-SUB-30X38-5EN1': '19HT4Fl2InGVcmjyJ0GXBInoSrSV7k0B9',
  'PLANCHA-SUB-30X38-8EN1': '19Rj1TjoTArmrhemIZb35wD6DaZJhp4Vn',
  'PLANCHA-SUB-40X60': '1WsdQi1n3TIBqPFQWEGZmQG6JdNjCBjgt',
  'PLANCHA-SUB-AUTO-38X38': '1yOkQIqzZIf5QU9YWz9uAlG0819nXtiS9',
  'PLANCHA-SUB-AUTO-GORRA': '1VyjCxYlB4zXEh_wYOdj0hsScFgg0_xM1',
  'PLANCHA-SUB-AUTO-TERMO': '1STwGhTN_SwSee26TNQOjj8djMaywwHEi',
  'PLANCHA-SUB-GORRA': '19vzDUG7gRdVy9K8NptIxUpgAckHlOKjB',
  'PLANCHA-SUB-GORRA-PORT': '1y_6nVbzMuTPhpM7VHWmUscS6OJlz2scS',
  'PLANCHA-SUB-PORTATIL': '1_feMTm7dBE2WY1qY7-XEMGcb0egw6YeR',
  'PLANCHA-SUB-TAZA': '1WETowZEqFUQcmNc52Zz2sOq_KQDBpjms',
  'PLANCHA-SUB-TERMO': '1Lr52VEHHIUZHPiY_4OHWiI9x2LtvwhFL',
  'PPF-BKG-152X15': '1OqD0W4wHt9K7a-1bRshK6ayJ86nPRu-y',
  'PPF-BKM-152X15': '1bJyzEpRebCGXLYX49Ny55ZfDFnJZDIJY',
  'PPF-G-152X15': '1ckJGAUiKQsGOCPQliIft_g1lAX3HAGUW',
  'PPF-M-152X15': '1mZHeTOADteqs7AyJlxLzau1Qc4lLRY4t',
  'PUNAX-75G-A4': '1eAIvLOtCjvKxmKZZl5ibNzsZ1FQmJh4t',
  'PVSUB-MDF-ROUND': '1idGaXK6xuWn2YnpdxtzROefp6fk5fkBn',
  'PVSUB-MDF-SQUARE': '1KWMt8o0Udsefgx5q1Xs6pguyrfjo0OBK',
  'RCSUB-CORA-16P': '1g9NhCv1r3_DMU5ZGHB2k0-cY7VSzTjSH',
  'RCSUB-SQUARE-40P': '1RzPDMWrvSzHIGKc358XeKFYfKO1i70cZ',
  'REPORT-75G-OF': '1uRXHZDxxqHjv0ry-31zjH5JZbUgTuUcZ',
  'RESISTENCIA-TAZA-C12': '1sqXwPzsHYqXTVIBV0n0ENVZhYH7QSCAE',
  'RESISTENCIA-TAZA-C17': '1QbkNqC9pPwBw5IQwfHMfZq_EfMy4_5hF',
  'RESISTENCIA-TAZA-R11': '1eAlx_AEu4NTWhCKTAY8UOfp94qPUsxRC',
  'RESISTENCIA-TAZA-R9': '13OXr0VuK2r6R57L99HkLIC1GBdIRbZsB',
  'RESISTENCIA-TERMO-R30': '1jnqX94zmkJKFh7HwztKenpXvsVBAQqnG',
  'SEW-12ST': '1Yat5T3GvHL4h8p4ZhUKqtp1a3vI_SiMj',
  'SEW-MINI': '1KoH999MqudPBxbOImi2c_fySS9jDdZgX',
  'SMARTLOCK-B1': '1gyc6O6L0zLcNVzBTNMMDNeaE0l48ByPc',
  'SMARTLOCK-WT1': '1ZDL-afa2wvSQ0NI0yFDgf6BrEnwuzhI5',
  'SPC-1220X180X4MM-0.5L-1IX-W1357L': '1sqHldP1fix13YuEX_B6xbEsEU5X78Ac1',
  'SPC-1220X180X4MM-0.5L-6099-9': '1kau7Ame5mxRNBu0II3xnQ-6dGU8Eiswr',
  'SPC-1220X180X4MM-0.5L-M0051-1': '1qH0Y7waENRRGGz6T7fhvNuFHWV0m93IE',
  'SPC-1220X180X4MM-0.5L-W1357L': '1T4vbi9gRcQNX7pdODoM5sbrrjHaJdlcU',
  'SSRULE-60CM': '1bmEuUdVVkvn2recrGYBfs5n4D1iTVCeH',
  'SWFBK-15%-152X30': '16jS2BDa7gX0sFtt8Py42qd0CZI40yA7S',
  'TAPAA4SLV50': '1uoCieutDX33ra0c03-SYRrXkW8OT0F6j',
  'TAZASUB-CORA-CER-11OZ-WG': '1jSZA6LPP866tKxYybu4MbUhuNu4owxxF',
  'TAZASUB-CORA-MAGIC-CER-11OZ-BK': '16NC4Ai6hQMlSyQD9_MvcKV9RT7BFswCm',
  'TAZASUB-GLIT-CER-11OZ-GLD': '1Rgzlwb_GSNbPPKrXZTjXIFD8DpEKopgC',
  'TAZASUB-GLIT-CER-11OZ-SLV': '1g8rxN0gYVO0yP2OxXQQrP5f8JvyO2rd6',
  'TAZASUB-MAGIC-CER-11OZ-BK': '17NsaEn3DffUYtxYCEcJUlas0jCigAzx_',
  'TAZASUB-MAGIC-CER-11OZ-BL': '1eL6BGsaek21CDAHjVwYFki5cImCJZeAG',
  'TAZASUB-MAGIC-CER-11OZ-RD': '1bhVfJ-lIrC8PtVgyKBwHd5-RcaV2dpso',
  'TAZASUB-PRL-CER-11OZ-GLD': '1tUjWdJvA-sMa-KMHF_HPQ6D-2VCME_sg',
  'TAZASUB-PRL-CER-11OZ-PK': '1XF_DQ_ZhWy_mkPmx3mAyt-b82PeFiGxe',
  'TAZASUB-PRL-CER-11OZ-SLV': '1uPgX6aN3YC_nCCTpX0ThmpZ9Hpjce7iU',
  'TAZASUB-ST-CER-11OZ-WG': '1lGE7Sra-4m4_Waksc4n6ekU4qRBpzeaU',
  'TELATEFLON-SUB-30X38': '16EtvF2vOTH4k2GdkA4U8BbFEhzlfw1ny',
  'TELATEFLON-SUB-40X60': '1tWiGG7mn6Qjs5H6dIspPGwYXeOYVg_ZT',
  'TERMOSUB-ALU-500ML-W': '18RvpIrVblscrJyOKpNyk07AF47Hs3V44',
  'TERMOSUB-DTEMP-500ML-W': '18qtejik6r-gKwhDpsa6MUa-TXwHzVK7I',
  'TSHIRTGUIDERULE-AIO': '1TLp_RyVrXk5T0HwKEtuzPN4PmavbDkI7',
  'TSHIRTSUB-POLY-2-L-W': '1-qkK3eA0X1WtNNpUgM2FEZCTNSHiGrTN',
  'TSHIRTSUB-POLY-2-S-W': '1lp6d8NpOxKAm7qSV_oEiuA_ZVR1HcDo9',
  'TSHIRTSUB-POLY-2-XXL-W': '1lpid9u3B9j6xGm3fAQR8U2XugmogrRjw',
  'TSHIRTSUB-POLY-L-W': '1qG7UtVu0ZgnXMiv6L-mego6a1K9_HcWv',
  'TSHIRTSUB-POLY-S-W': '1pHynDgU0eHv-RtSkuEjE1A88JONJi_cv',
  'TSHIRTSUB-POLY-XXL-W': '16hO_fINco0Uy4MJrnLTPUewpcKZX7VN7',
  'TUBEQ-LAM-230MM': '19uSWvb_FH7vL7LascRYN4A-BcyPq52Dt',
  'TUBEQ-LAM-240MM': '1uLLxusKbzVM0oWmwlrKD0CvpkWd7vedj',
  'TUBEQ-LAM-330MM': '1m1eXnBxanLQ1hBHWcmBKTe-j0tIqzt8l',
  'TUMBLERSUB-ALU-1200ML-W': '1639iQiJb3ZRY0miJsCQGu0dASr3mJSMi',
  'WEEDINGTOOLS-SETX6': '1zT8Ej3eNAMss0JLTCSSf4bh7pPExROgi',
  'WFBK-15%-152X30': '1aZPYFagH6874SomFaa-opUoGQHQFCG6G',
  'WFBK-35%-152X30': '1ZhcV0gIzMSk5Wm-MqFzUBJA2CCBidcuG',
  'WFBK-5%-152X30': '1BJz2zx_i4FJ1f4EFuqi4uAhOswbHnBbi',
  'WPC-2900X150X12MM-DP2485': '1Ok_opXLih3xNJzullOjfqEdT2mj2BixO',
  'WPC-2900X150X12MM-DW2501': '1wNUr-Lm0qWTiBfGPjXzBXZrXHGIv3gps',
  'WPC-2900X150X12MM-DW2505': '1FnOZl39rWlgWVIrSG-4syM2wFAJNXC6m',
  'WPC-2900X150X12MM-DW2513': '1AmxIeFX4Rspp2eOx6inMs5AaGYKOZX3k'
};

function findFileIdForSku(sku) {
  if (!sku) return null;
  var s    = sku.trim().toUpperCase();
  var keys = Object.keys(SKU_IMAGES);

  // 1. Exact match (case-insensitive)
  for (var i = 0; i < keys.length; i++) {
    if (keys[i].toUpperCase() === s) return SKU_IMAGES[keys[i]];
  }

  // 2. Strip suffix segments one by one (GORRATRUCKERSUB-BK → GORRATRUCKERSUB → ...)
  var parts = s.split('-');
  for (var si = parts.length - 1; si >= 1; si--) {
    var cand = parts.slice(0, si).join('-');
    for (var j = 0; j < keys.length; j++) {
      if (keys[j].toUpperCase() === cand) return SKU_IMAGES[keys[j]];
    }
  }

  // 3. Longest key that is a prefix of s (TAZASUB-... → TAZAS)
  var best = null, bestLen = 0;
  for (var ki = 0; ki < keys.length; ki++) {
    var ku = keys[ki].toUpperCase();
    if (s.indexOf(ku) === 0 && ku.length > bestLen) {
      best = keys[ki]; bestLen = ku.length;
    }
  }
  if (best) return SKU_IMAGES[best];

  return null;
}

// ---------------------------------------------------------------
// Imágenes de productos — llamado desde el cliente via google.script.run.
// Busca el Drive file ID para cada SKU, descarga thumbnails en paralelo
// y los devuelve como base64 data URLs. Cache 24 h por fileId.
// ---------------------------------------------------------------

function getSheetImages(sheetName) {
  var result = {};
  var token  = ScriptApp.getOAuthToken();
  var cache  = CacheService.getScriptCache();

  var sheet = SpreadsheetApp.openById(SPREADSHEET_ID).getSheetByName(sheetName);
  if (!sheet) return {};

  var values       = sheet.getDataRange().getValues();
  var fileIdToRows = {};
  var rowToFileId  = {};

  for (var vi = 0; vi < values.length; vi++) {
    var v = values[vi][0];
    if (!v) continue;
    var sku    = String(v).trim();
    var row    = vi + 1;
    var fileId = findFileIdForSku(sku);
    if (!fileId) continue;
    rowToFileId[row] = fileId;
    if (!fileIdToRows[fileId]) fileIdToRows[fileId] = [];
    fileIdToRows[fileId].push(row);
  }

  var fileIds = Object.keys(fileIdToRows);
  if (fileIds.length === 0) return {};

  // Check cache
  var cacheKeys    = fileIds.map(function(id){ return 'drv_' + id; });
  var cachedValues = cache.getAll(cacheKeys);
  var needFetch    = [];

  for (var fi = 0; fi < fileIds.length; fi++) {
    var fid  = fileIds[fi];
    var cval = cachedValues['drv_' + fid];
    if (cval) {
      var rows = fileIdToRows[fid];
      for (var ri = 0; ri < rows.length; ri++) result[rows[ri]] = cval;
    } else {
      needFetch.push(fid);
    }
  }

  if (needFetch.length === 0) return result;

  // Batch-fetch Drive thumbnails in parallel
  var requests = needFetch.map(function(fid) {
    return {
      url: 'https://drive.google.com/thumbnail?id=' + fid + '&sz=w400',
      headers: {Authorization: 'Bearer ' + token},
      muteHttpExceptions: true
    };
  });

  var responses = UrlFetchApp.fetchAll(requests);

  for (var ri2 = 0; ri2 < responses.length; ri2++) {
    var resp = responses[ri2];
    var fid  = needFetch[ri2];
    if (resp.getResponseCode() !== 200) continue;

    var blob    = resp.getBlob();
    var ct      = blob.getContentType() || 'image/jpeg';
    var dataUrl = 'data:' + ct + ';base64,' + Utilities.base64Encode(blob.getBytes());

    var rows2 = fileIdToRows[fid];
    for (var ri3 = 0; ri3 < rows2.length; ri3++) result[rows2[ri3]] = dataUrl;

    if (dataUrl.length < 95000) cache.put('drv_' + fid, dataUrl, 86400);
  }

  return result;
}

// ---------------------------------------------------------------
// Parseo de hojas
// ---------------------------------------------------------------

function parseSheet(sheet) {
  var data     = sheet.getDataRange();
  var rows     = data.getValues();
  var formulas = data.getFormulas();

  var products = [], currentCat = '';
  for (var i = 0; i < rows.length; i++) {
    var row  = rows[i];
    if (!row[0]) continue;
    var cell = String(row[0]).trim();
    if (cell === 'GLOBAL' || cell === 'SKU' || cell === 'Echeq 30' ||
        cell.indexOf('LISTA DE PRECIOS') !== -1 || cell.indexOf('Vigencia') !== -1) continue;
    if (row.length < 3 || !row[2]) { currentCat = cell; continue; }
    if (String(row[3]).indexOf('Cant') !== -1 || String(row[3]).indexOf('mt2') !== -1) continue;
    if (String(row[2]) !== 'DISPONIBLE' && String(row[2]) !== 'SIN STOCK') {
      currentCat = cell; continue;
    }

    // URL directa si la col J tiene fórmula =IMAGE("url")
    var imgUrl = '';
    if (formulas[i] && formulas[i][9]) {
      var m = formulas[i][9].match(/IMAGE\(["\']([^"\']+)["\']/i);
      if (m) imgUrl = m[1];
    }

    products.push({
      sku:       String(row[0]),
      nombre:    String(row[1]),
      stock:     String(row[2]),
      categoria: currentCat || sheet.getName(),
      cant1: String(row[3] || ''), precio1: String(row[4] || ''),
      cant2: String(row[5] || ''), precio2: String(row[6] || ''),
      cant3: String(row[7] || ''), precio3: String(row[8] || ''),
      sheetRow: i + 1,
      imgUrl:   imgUrl
    });
  }
  return products;
}

// ---------------------------------------------------------------
// Renderizado de tarjetas y secciones
// ---------------------------------------------------------------

function formatPrice(pr) {
  if (!pr || pr === '-' || pr === '') return pr;
  var s = String(pr);
  var m = s.match(/^([A-Za-z$\s]*)([\d,.]+)(.*)/);
  if (!m) return pr;
  var num = parseFloat(m[2].replace(',', '.'));
  if (isNaN(num)) return pr;
  return m[1] + num.toFixed(2) + m[3];
}

function buildCard(p, sheetName) {
  var avail = p.stock === 'DISPONIBLE';

  // Si hay URL directa (formula IMAGE), úsala; sino carga lazy desde Drive
  var imgHtml;
  if (p.imgUrl) {
    imgHtml = '<img src="' + p.imgUrl + '" alt="' + p.sku
            + '" loading="lazy" onerror="this.style.display=\'none\'">';
  } else {
    imgHtml = '<img src="" class="lazy-img"'
            + ' data-sheet="' + sheetName + '"'
            + ' data-row="'   + p.sheetRow + '"'
            + ' alt="'        + p.sku + '">';
  }

  var badge = avail
    ? '<span class="avail">✓ Disponible</span>'
    : '<span class="unavail">✗ Sin stock</span>';
  var prices = '';
  var tiers = [[p.cant1, p.precio1],[p.cant2, p.precio2],[p.cant3, p.precio3]];
  for (var t = 0; t < tiers.length; t++) {
    var c = tiers[t][0], pr = tiers[t][1];
    if (pr && pr !== '-' && pr !== '') {
      var cls = t === 1 ? ' price-best' : '';
      prices += '<div class="price-row' + cls + '"><span>x' + c + ' u.</span>'
              + '<span>' + formatPrice(pr) + '</span></div>';
    }
  }
  var nombre = p.nombre.length > 72 ? p.nombre.substring(0, 72) + '…' : p.nombre;
  return '<div class="card' + (avail ? '' : ' dim') + '">'
    + '<div class="card-img">' + imgHtml + '</div>'
    + '<div class="card-body">'
    + '<div class="card-sku">' + p.sku + '</div>'
    + '<div class="card-name">' + nombre + '</div>'
    + badge
    + (prices ? '<div class="prices">' + prices + '</div>' : '')
    + '</div></div>';
}

function buildSection(sheetName, products) {
  var meta = {
    'Sublimación':               {icon:'🔥', color:'#FF6B35'},
    'Laminación':                {icon:'✨', color:'#26A69A'},
    'Papelería':                 {icon:'📄', color:'#5C6BC0'},
    'Kraft':                     {icon:'📦', color:'#8D6E63'},
    'Domótica':                  {icon:'🏠', color:'#00897B'},
    'Automotor':                 {icon:'🚗', color:'#E53935'},
    'Revestimiento':             {icon:'🪟', color:'#7B1FA2'},
    'Cartelería':                {icon:'🖼️', color:'#F4511E', label:'Cartelería & Gran Formato'},
    'Vinilos Termotransferibles':{icon:'👕', color:'#D81B60'}
  };
  var m     = meta[sheetName] || {icon:'📦', color:'#00BCD4'};
  var label = m.label || sheetName;
  var avail = products.filter(function(p){return p.stock==='DISPONIBLE';}).length;

  var byCat = {}, catOrder = [];
  for (var i = 0; i < products.length; i++) {
    var cat = products[i].categoria;
    if (!byCat[cat]) { byCat[cat] = []; catOrder.push(cat); }
    byCat[cat].push(products[i]);
  }

  var cardsHtml = '';
  for (var ci = 0; ci < catOrder.length; ci++) {
    var cat = catOrder[ci];
    var ps  = byCat[cat];
    if (cat && cat !== sheetName)
      cardsHtml += '<div class="subcat-label">' + cat + '</div>';
    for (var pi = 0; pi < ps.length; pi++)
      cardsHtml += buildCard(ps[pi], sheetName);
  }

  return '<section class="cat-section" id="sec-' + sheetName.replace(/[^a-zA-Z]/g,'') + '">'
    + '<div class="cat-head" style="--accent:' + m.color + '">'
    + '<div class="cat-head-left">'
    + '<div class="cat-icon-wrap" style="background:' + m.color + '">' + m.icon + '</div>'
    + '<div><div class="cat-tag">Categoría</div><h2>' + label + '</h2></div></div>'
    + '<div class="cat-badge">' + avail + ' disponibles</div>'
    + '</div>'
    + '<div class="cards-grid">' + cardsHtml + '</div>'
    + '</section>';
}

// ---------------------------------------------------------------
// Entry point
// ---------------------------------------------------------------

function doGet() {
  var ss         = SpreadsheetApp.openById(SPREADSHEET_ID);
  var vigencia   = '';
  var sheetOrder = ['Sublimación','Laminación','Papelería','Kraft','Automotor',
                    'Domótica','Revestimiento','Cartelería','Vinilos Termotransferibles'];
  var navLinks = '', sectionsHtml = '';

  for (var si = 0; si < sheetOrder.length; si++) {
    var sheetName = sheetOrder[si];
    var sheet     = ss.getSheetByName(sheetName);
    if (!sheet) continue;
    if (!vigencia) {
      var v = sheet.getRange('A3').getValue();
      vigencia = v ? String(v) : 'Junio 2026';
    }
    var products = parseSheet(sheet);
    if (products.length === 0) continue;
    var icons = {'Sublimación':'🔥','Laminación':'✨','Papelería':'📄','Kraft':'📦',
                 'Domótica':'🏠','Automotor':'🚗','Revestimiento':'🪟',
                 'Cartelería':'🖼️','Vinilos Termotransferibles':'👕'};
    navLinks += '<a href="#sec-' + sheetName.replace(/[^a-zA-Z]/g,'') + '" class="nav-link">'
              + (icons[sheetName]||'📦') + ' ' + sheetName + '</a>';
    sectionsHtml += buildSection(sheetName, products);
  }

  var logoDataUrl = getLogoDataUrl();
  var bannerUrl   = 'https://drive.google.com/thumbnail?id=' + BANNER_FILE_ID + '&sz=w1200';

  var html = HtmlService.createHtmlOutput(
    getHtml(vigencia, navLinks, sectionsHtml, bannerUrl, logoDataUrl, JSON.stringify(sheetOrder))
  );
  html.setTitle('Catálogo Global Electronics');
  html.setXFrameOptionsMode(HtmlService.XFrameOptionsMode.ALLOWALL);
  return html;
}

// ---------------------------------------------------------------
// HTML
// ---------------------------------------------------------------

function getHtml(vigencia, navLinks, sectionsHtml, bannerUrl, logoDataUrl, sheetOrderJson) {
  var logoHtml = logoDataUrl
    ? '<img src="' + logoDataUrl + '" alt="Global Electronics" class="logo-img">'
    : '<svg class="logo-img" viewBox="0 0 160 52" xmlns="http://www.w3.org/2000/svg">'
      + '<rect width="160" height="52" rx="8" fill="rgba(255,255,255,.2)"/>'
      + '<text x="80" y="30" text-anchor="middle" font-family="Nunito,sans-serif" font-weight="900" font-size="24" fill="white">Global</text>'
      + '<text x="80" y="45" text-anchor="middle" font-family="Nunito,sans-serif" font-weight="700" font-size="10" fill="rgba(255,255,255,.75)" letter-spacing="2">ELECTRONICS</text>'
      + '</svg>';

  var lazyScript = '<script>'
    + '(function(){'
    + '  if(typeof google==="undefined"||!google.script)return;'
    + '  var sheets=' + sheetOrderJson + ';'
    + '  function load(sn){'
    + '    google.script.run'
    + '      .withSuccessHandler((function(s){return function(m){'
    + '        if(!m)return;'
    + '        var rows=Object.keys(m);'
    + '        for(var i=0;i<rows.length;i++){'
    + '          var imgs=document.querySelectorAll(\'.lazy-img[data-sheet="\'+s+\'"][data-row="\'+rows[i]+\'"]\');'
    + '          for(var j=0;j<imgs.length;j++)imgs[j].src=m[rows[i]];'
    + '        }'
    + '      };})(sn))'
    + '      .withFailureHandler(function(){})'
    + '      .getSheetImages(sn);'
    + '  }'
    + '  if(document.readyState==="loading"){'
    + '    document.addEventListener("DOMContentLoaded",function(){sheets.forEach(load);});'
    + '  } else { sheets.forEach(load); }'
    + '})();'
    + '</script>';

  return '<!DOCTYPE html><html lang="es"><head>'
    + '<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
    + '<title>Catálogo Global Electronics</title>'
    + '<link href="https://fonts.googleapis.com/css2?family=Nunito:wght@400;600;700;800;900&display=swap" rel="stylesheet">'
    + '<style>' + getCSS() + '</style></head><body>'

    + '<nav class="topnav">'
    + '<div class="nav-logo">' + logoHtml + '</div>'
    + '<div class="nav-links">' + navLinks + '</div>'
    + '<div class="nav-vigencia">📅 ' + vigencia + '</div>'
    + '</nav>'

    + '<div class="cover">'
    + '<div class="cover-eyebrow">📘 CATÁLOGO MAYORISTA</div>'
    + '<h1>Lista de Precios<em>Oficial</em></h1>'
    + '<p class="cover-sub">Equipos, insumos y artículos para profesionales del estampado, la impresión y la papelería.</p>'
    + '<div class="cover-banner"><img src="' + bannerUrl + '" alt="Productos Global Electronics"/></div>'
    + '<p class="cover-bottom">globalecom.ar · ' + vigencia + ' · Precios en USD sin IVA</p>'
    + '</div>'

    + '<div class="catalog">' + sectionsHtml + '</div>'

    + '<footer><strong>Global Electronics</strong> · globalecom.ar<br>'
    + vigencia + ' · Precios en USD sin IVA · Sujeto a cambios sin previo aviso</footer>'

    + lazyScript
    + '</body></html>';
}

// ---------------------------------------------------------------
// CSS
// ---------------------------------------------------------------

function getCSS() {
  return ':root{--teal:#00BCD4;--teal-dark:#0097A7;--teal-light:#E0F7FA;--text:#1C2B36;--gray:#6B7C8D;--bg:#F5F9FB;--white:#fff;--radius:16px}'
    + '*{box-sizing:border-box;margin:0;padding:0}'
    + 'body{font-family:Nunito,sans-serif;background:var(--bg);color:var(--text)}'

    + '.topnav{position:sticky;top:0;z-index:100;background:linear-gradient(135deg,#006064,#00BCD4);'
    + 'padding:12px 24px;display:flex;align-items:center;gap:16px;flex-wrap:wrap;'
    + 'box-shadow:0 2px 12px rgba(0,0,0,.2)}'
    + '.nav-logo{display:flex;align-items:center}'
    + '.logo-img{height:44px;width:auto;display:block}'
    + '.nav-links{display:flex;gap:8px;flex-wrap:wrap;flex:1}'
    + '.nav-link{background:rgba(255,255,255,.15);color:white;text-decoration:none;'
    + 'padding:6px 14px;border-radius:50px;font-size:.78rem;font-weight:700;'
    + 'transition:background .2s;white-space:nowrap}'
    + '.nav-link:hover{background:rgba(255,255,255,.3)}'
    + '.nav-vigencia{color:rgba(255,255,255,.7);font-size:.78rem;font-weight:700;white-space:nowrap}'

    + '.cover{background:linear-gradient(160deg,#006064 0%,#00BCD4 55%,#4DD0E1 100%);'
    + 'padding:60px 24px;display:flex;flex-direction:column;align-items:center;text-align:center}'
    + '.cover-eyebrow{background:rgba(255,255,255,.15);border:1.5px solid rgba(255,255,255,.3);'
    + 'color:white;padding:6px 18px;border-radius:50px;font-weight:800;font-size:.8rem;'
    + 'letter-spacing:2px;margin-bottom:16px}'
    + '.cover h1{color:white;font-size:clamp(2.5rem,6vw,5rem);font-weight:900;line-height:1.05;margin-bottom:12px}'
    + '.cover h1 em{font-style:normal;color:#B2EBF2;display:block;font-size:.7em}'
    + '.cover-sub{color:rgba(255,255,255,.8);font-size:1rem;max-width:500px;margin-bottom:32px;line-height:1.7}'
    + '.cover-banner{width:100%;max-width:900px;border-radius:16px;overflow:hidden;'
    + 'box-shadow:0 20px 60px rgba(0,0,0,.25);margin-bottom:32px}'
    + '.cover-banner img{width:100%;display:block}'
    + '.cover-bottom{color:rgba(255,255,255,.5);font-size:.8rem}'

    + '.catalog{max-width:1280px;margin:0 auto;padding:40px 16px}'
    + '.cat-section{background:white;border-radius:20px;margin-bottom:36px;'
    + 'box-shadow:0 2px 16px rgba(0,0,0,.06);overflow:hidden}'
    + '.cat-head{padding:24px 28px;display:flex;align-items:center;justify-content:space-between;'
    + 'gap:16px;flex-wrap:wrap;border-left:6px solid var(--accent)}'
    + '.cat-head-left{display:flex;align-items:center;gap:16px}'
    + '.cat-icon-wrap{width:56px;height:56px;border-radius:14px;display:flex;align-items:center;'
    + 'justify-content:center;font-size:1.8rem;flex-shrink:0}'
    + '.cat-tag{font-size:.68rem;font-weight:900;letter-spacing:2px;color:var(--gray);text-transform:uppercase;margin-bottom:2px}'
    + '.cat-head h2{font-size:1.4rem;font-weight:900;color:var(--text)}'
    + '.cat-badge{background:var(--teal-light);color:var(--teal-dark);padding:6px 16px;'
    + 'border-radius:50px;font-weight:800;font-size:.8rem;white-space:nowrap}'

    + '.subcat-label{grid-column:1/-1;background:#F0F4F8;padding:10px 16px;'
    + 'font-size:.78rem;font-weight:900;color:var(--gray);text-transform:uppercase;letter-spacing:1px}'

    + '.cards-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(210px,1fr));'
    + 'gap:1px;background:#F0F4F8}'
    + '.card{background:white;display:flex;flex-direction:column;transition:box-shadow .2s}'
    + '.card:hover{box-shadow:0 6px 24px rgba(0,188,212,.15);z-index:1;position:relative}'
    + '.card.dim{opacity:.4}'
    + '.card-img{height:180px;overflow:hidden;background:#F5F9FB;display:flex;'
    + 'align-items:center;justify-content:center}'
    + '.card-img img{width:100%;height:100%;object-fit:cover;transition:transform .3s}'
    + '.card-img img:not([src]){display:none}'
    + '.card-img img[src=""]{display:none}'
    + '.card:hover .card-img img{transform:scale(1.05)}'
    + '.no-img{font-size:3rem;color:#CBD5E0}'
    + '.card-body{padding:12px;display:flex;flex-direction:column;gap:6px;flex:1}'
    + '.card-sku{font-size:.66rem;color:var(--teal-dark);font-weight:900;letter-spacing:.5px;text-transform:uppercase}'
    + '.card-name{font-size:.8rem;color:var(--text);font-weight:600;line-height:1.4;flex:1}'
    + '.avail{background:#E8F5E9;color:#2E7D32;font-size:.68rem;font-weight:800;padding:2px 8px;border-radius:20px;width:fit-content}'
    + '.unavail{background:#FFEBEE;color:#C62828;font-size:.68rem;font-weight:800;padding:2px 8px;border-radius:20px;width:fit-content}'
    + '.prices{display:flex;flex-direction:column;gap:2px;margin-top:2px}'
    + '.price-row{display:flex;justify-content:space-between;font-size:.74rem;padding:3px 6px;border-radius:6px;background:#F5F9FB}'
    + '.price-best{background:var(--teal-light);font-weight:800;color:var(--teal-dark)}'
    + 'footer{background:#0E1F26;color:rgba(255,255,255,.5);padding:28px;text-align:center;font-size:.8rem}'
    + 'footer strong{color:white}'
    + '@media(max-width:600px){.topnav{flex-direction:column;align-items:flex-start}'
    + '.cards-grid{grid-template-columns:repeat(auto-fill,minmax(150px,1fr))}}';
}
