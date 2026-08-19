// Elun · 체크아웃 단일 정본
//   해외(영문): Digistore24 (2026-07-23 Paddle이 astrology 카테고리 거절 → 전환)
//   국내(/ko/): NHN KCP 표준결제 직접 연동 (2026-07-31 포트원 경유 → KCP 단독 전환)
// 이 파일 하나만 고치면 모든 페이지(index/ko/index, result/ko/result, 리포트 내 업그레이드 CTA)에 반영됩니다.
//
// ⚠️ 파일명(paddle-config.js)과 함수명(elunOpenPaddleCheckout)은 레거시입니다.
//    이미 배포된 리포트 HTML(elun-engine)이 이 파일을 이 이름으로 로드하고 이 함수를 호출하므로,
//    엔진 재배포 없이 결제사를 갈아끼우기 위해 이름을 유지합니다.
//
// 분기 규칙: <html lang="ko"> 이고 ELUN_CHECKOUT_KO 가 설정 완료(PASTE_ 없음)면 NHN KCP,
//            아니면 기존 Digistore24. → 채널키 발급 전까지 한국어 페이지도 DS24 로 폴백.
window.ELUN_CHECKOUT = {
  provider: "digistore24",
  // ⚠️ 2026-08-15: DS24 상품 승인 보류(컴플라이언스 서류 요청 미회신) → 상품 페이지가 403
  //    "this product cannot be purchased at this time" 를 반환한다.
  //    승인 완료 전까지 결제 버튼을 게이트한다. 승인되면 true 로만 바꾸면 즉시 열림.
  enabled: false,
  products: {
    single:  "714429",  // Elun Precision Report — $29
    decade:  "714430",  // Elun Precision Report + Decade — $49
    couple:  "714431",  // Elun Compatibility Report — $49
    upgrade: "714432",  // Elun Decade Upgrade — $25
  },
};

// ── 국내 결제 (NHN KCP 표준결제 — 직접 연동) ────────────────────────────
// 2026-07-31 실서비스 전환: 실 사이트코드 IP9HY · env=production.
//   Railway env 반영 완료: KCP_SITE_CD=IP9HY · KCP_ENV=production · KCP_CERT_INFO(PG-API 인증서 직렬화) · KCP_AMOUNT_*
//   KCP 서버IP 화이트리스트(취소용)에 Railway outbound 162.220.232.76 등록 완료.
//   ⚠️ 실제 카드 승인은 통신판매업 신고번호 → KCP 카드사 등록심사 통과 후 가능(심사 전 결제 시 카드사 미등록 에러).
//   금액 변경 시 Railway KCP_AMOUNT_* 도 같이 (서버가 승인금액 대조로 위변조 차단).
// 서버 규약 (elun-engine — 배포됨): POST https://api.elun.me/payment/kcp/approve
//   { enc_data, enc_info, tran_cd, ordr_no, ordr_mony, email, product }
window.ELUN_CHECKOUT_KO = {
  provider: "kcp",
  env:      "production",       // "test" | "production"
  siteCd:   "IP9HY",            // NHN KCP 실 사이트코드
  siteName: "Elun",             // 영문 상점명(PC 결제창 표기)
  amounts:  {                   // KRW — Railway KCP_AMOUNT_* 와 반드시 일치
    single:  29000,
    decade:  49000,
    couple:  49000,
    upgrade: 25000,
    year:    100000,
  },
  orderNames: {
    single:  "Elun 정밀 사주 리포트",
    decade:  "Elun 정밀 리포트 + 대운 10년",
    couple:  "Elun 커플 궁합 리포트",
    upgrade: "Elun 대운 10년 업그레이드",
    year:    "Elun 12개월 정밀 운세",
  },
};

// 리포트 클레임/승인을 호출할 API 베이스 (엔진).
window.ELUN_API_BASE = window.ELUN_API_BASE || "https://api.elun.me";

// 레거시 호환 shim — result.html 등이 window.ELUN_PADDLE.prices.* 로 "결제 설정됨" 여부를 검사함.
// 값은 실제로 사용되지 않고, PASTE_ 로 시작하지 않는 문자열이기만 하면 버튼이 켜집니다.
window.ELUN_PADDLE = {
  env: "production",
  clientToken: "digistore24",
  prices: {
    single:  window.ELUN_CHECKOUT.products.single,
    decade:  window.ELUN_CHECKOUT.products.decade,
    couple:  window.ELUN_CHECKOUT.products.couple,
    upgrade: window.ELUN_CHECKOUT.products.upgrade,
  },
};

function elunKoReady() {
  const k = window.ELUN_CHECKOUT_KO;
  return !!(k && k.siteCd && k.siteCd.indexOf("PASTE_") !== 0);
}

function elunIsKoPage() {
  return (document.documentElement.getAttribute("lang") || "").toLowerCase().indexOf("ko") === 0;
}

// ── NHN KCP 표준결제 스크립트 지연 로드 (PC 결제창) ──
// kcp_spay_hub.js 는 onload 직후가 아니라 약간 뒤에 KCP_Pay_Execute_Web 을 정의하므로 폴링 대기.
function elunLoadKcp(env) {
  return new Promise(function (resolve, reject) {
    function waitFn() {
      let tries = 0;
      (function poll() {
        if (window.KCP_Pay_Execute_Web) return resolve();
        if (++tries > 80) return reject(new Error("KCP function not ready"));
        setTimeout(poll, 50);
      })();
    }
    if (window.KCP_Pay_Execute_Web) return resolve();
    const existing = document.getElementById("elun-kcp-sdk");
    if (existing) return waitFn();
    const s = document.createElement("script");
    s.id = "elun-kcp-sdk";
    s.src = (env === "production"
             ? "https://spay.kcp.co.kr/plugin/kcp_spay_hub.js"
             : "https://testspay.kcp.co.kr/plugin/kcp_spay_hub.js");
    s.onload = waitFn;
    s.onerror = function () { reject(new Error("KCP script load failed")); };
    document.head.appendChild(s);
  });
}

// ── 이메일 수집 모달 (리포트 수령·주문 조회에 필요) ──
function elunAskEmail() {
  return new Promise(function (resolve) {
    const old = document.getElementById("elun-email-modal");
    if (old) old.remove();
    const wrap = document.createElement("div");
    wrap.id = "elun-email-modal";
    wrap.style.cssText = "position:fixed;inset:0;z-index:99999;background:rgba(8,6,4,.82);display:flex;align-items:center;justify-content:center;padding:20px";
    wrap.innerHTML =
      '<div style="max-width:400px;width:100%;background:#14100b;border:1px solid #c9a22755;border-radius:16px;padding:26px;font-family:inherit;color:#f3ece0">' +
      '<div style="font-size:16.5px;font-weight:700;margin-bottom:6px">리포트를 받을 이메일</div>' +
      '<div style="font-size:13px;color:#b8ab97;line-height:1.5;margin-bottom:14px">결제 확인과 리포트 재열람에 사용됩니다. 결제 후 이 이메일과 주문번호로 리포트를 여실 수 있어요.</div>' +
      '<input id="elun-email-input" type="email" placeholder="you@example.com" style="width:100%;box-sizing:border-box;background:#0e0b08;border:1px solid #3a3226;border-radius:10px;color:#f3ece0;padding:12px;font-size:15px;outline:none" />' +
      '<div id="elun-email-err" style="font-size:12px;color:#d9807a;margin-top:6px;display:none">이메일 형식을 확인해주세요.</div>' +
      '<label id="elun-agree-box" style="display:flex;gap:9px;align-items:flex-start;margin-top:15px;font-size:12.5px;color:#b8ab97;line-height:1.5;cursor:pointer;border:1px solid #3a3226;border-radius:10px;padding:11px 12px;background:#0e0b08;transition:border-color .15s">' +
      '<input id="elun-agree" type="checkbox" style="margin-top:2px;flex:none;width:16px;height:16px;accent-color:#c9a227" />' +
      '<span>[필수] 본 상품은 즉시 제공되는 디지털콘텐츠이며, 리포트 생성·열람 후에는 「전자상거래법」 제17조에 따라 청약철회가 제한됨에 동의합니다.</span>' +
      '</label>' +
      '<div id="elun-agree-err" style="font-size:13px;font-weight:700;color:#e2564a;margin-top:8px;display:none">↑ 위 필수 동의에 체크해주세요 — 체크 후 결제창이 열립니다.</div>' +
      '<div style="display:flex;gap:10px;margin-top:16px">' +
      '<button id="elun-email-cancel" style="flex:1;background:transparent;border:1px solid #3a3226;border-radius:24px;color:#b8ab97;padding:11px;font-size:14px;cursor:pointer">취소</button>' +
      '<button id="elun-email-ok" style="flex:2;background:#c9a227;border:none;border-radius:24px;color:#14100b;font-weight:700;padding:11px;font-size:14px;cursor:pointer">결제 계속하기</button>' +
      "</div></div>";
    document.body.appendChild(wrap);
    const input = wrap.querySelector("#elun-email-input");
    const err = wrap.querySelector("#elun-email-err");
    function done(v) { wrap.remove(); resolve(v); }
    const agree = wrap.querySelector("#elun-agree");
    const agreeErr = wrap.querySelector("#elun-agree-err");
    agree.addEventListener("change", function () {
      if (agree.checked) {
        agreeErr.style.display = "none";
        wrap.querySelector("#elun-agree-box").style.borderColor = "#c9a227";
      }
    });
    function submit() {
      const v = (input.value || "").trim();
      if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(v)) { err.style.display = "block"; input.focus(); return; }
      if (!agree.checked) {
        agreeErr.style.display = "block";
        const box = wrap.querySelector("#elun-agree-box");
        box.style.borderColor = "#e2564a";
        box.scrollIntoView({ block: "center", behavior: "smooth" });
        box.animate([{transform:"translateX(0)"},{transform:"translateX(-6px)"},{transform:"translateX(6px)"},
                     {transform:"translateX(-4px)"},{transform:"translateX(0)"}], {duration: 320});
        return;
      }  // 전자상거래법 청약철회 제한 동의 필수
      done(v);
    }
    wrap.querySelector("#elun-email-ok").onclick = submit;
    wrap.querySelector("#elun-email-cancel").onclick = function () { done(null); };
    input.addEventListener("keydown", function (e) { if (e.key === "Enter") submit(); });
    setTimeout(function () { input.focus(); }, 50);
  });
}

// ── 모바일 기기 감지 (KCP PC 결제창은 모바일 미지원 → 모바일 표준결제로 분기) ──
function elunIsMobile() {
  const ua = navigator.userAgent || "";
  if (/Android|iPhone|iPod|Windows Phone/i.test(ua)) return true;
  // iPadOS 13+ 는 데스크톱 UA(Macintosh)를 쓰므로 터치 지점으로 판별
  if (/iPad/i.test(ua) || (/Macintosh/i.test(ua) && navigator.maxTouchPoints > 1)) return true;
  return false;
}

// ── NHN KCP 모바일 표준결제 (거래등록 + 전체 페이지 redirect) ──
// 흐름: 서버 /payment/kcp/mobile/register 로 거래등록(PayUrl·approval_key 수령)
//   → PayUrl 기반 encodingFilter.jsp 로 form POST(페이지 이동) → KCP 모바일 결제창
//   → 인증 후 KCP가 서버 Ret_URL 로 결과 POST → 서버가 승인 → 리포트로 redirect.
//   실패 시 서버가 /ko/?payerr=사유 로 되돌려줌 (아래 payerr 배너가 표시).
async function elunOpenKcpMobileCheckout(priceKey, email, opts) {
  let reg;
  try {
    const r = await fetch(window.ELUN_API_BASE + "/payment/kcp/mobile/register", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ product: priceKey, email: email,
                             redirect_to: opts.redirectTo || "report.html" }),
    });
    if (!r.ok) throw new Error((await r.json().catch(function(){return {};})).detail || "register failed");
    reg = await r.json();
  } catch (e) {
    alert("결제 준비에 실패했습니다. 잠시 후 다시 시도해주세요.\n(" + (e.message || e) + ")");
    return;
  }
  const P = {
    site_cd: reg.site_cd, pay_method: "CARD", currency: "410",   // 모바일은 KRW=410 (PC의 "WON" 넣으면 M015)
    shop_name: window.ELUN_CHECKOUT_KO.siteName || "Elun",
    ordr_idxx: reg.ordr_idxx, good_name: reg.good_name, good_mny: reg.good_mny,
    Ret_URL: reg.Ret_URL, approval_key: reg.approval_key, PayUrl: reg.PayUrl,
    buyr_mail: email,
  };
  const old = document.getElementById("elun-kcp-mform");
  if (old) old.remove();
  const form = document.createElement("form");
  form.id = "elun-kcp-mform"; form.name = "order_info"; form.method = "post";
  form.acceptCharset = "UTF-8";
  form.style.display = "none";
  Object.keys(P).forEach(function (k) {
    const i = document.createElement("input");
    i.type = "hidden"; i.name = k; i.value = P[k];
    form.appendChild(i);
  });
  // KCP 관례: PayUrl 디렉터리의 encodingFilter.jsp 를 거쳐 mobileGW 로 진입
  form.action = reg.PayUrl.substring(0, reg.PayUrl.lastIndexOf("/")) + "/jsp/encodingFilter/encodingFilter.jsp";
  document.body.appendChild(form);
  form.submit();   // 전체 페이지 이동 — 결제 후 서버 Ret_URL 이 리포트로 복귀시킴
}

// ── NHN KCP 결제 실행 (PC 표준결제창) ──
// 흐름: 이메일 수집 → order_info 폼 생성 → KCP 결제창 → 인증완료 시 KCP가 m_Completepayment 호출
//   → enc_data/enc_info/tran_cd 를 서버 /payment/kcp/approve 로 승인요청 → 성공 시 report 이동.
// opts: { redirectTo: 성공 후 이동(기본 "report.html"), includeOrder: 리다이렉트에 주문번호 포함(기본 true) }
async function elunOpenKcpCheckout(priceKey, opts) {
  opts = opts || {};
  const cfg = window.ELUN_CHECKOUT_KO;
  const amount = cfg.amounts[priceKey];
  const orderName = cfg.orderNames[priceKey] || "Elun Report";
  if (!amount) { alert("결제 설정 오류 — hello@elun.me 로 알려주세요."); return; }

  const email = await elunAskEmail();
  if (!email) return;

  if (elunIsMobile()) { elunOpenKcpMobileCheckout(priceKey, email, opts); return; }

  try { await elunLoadKcp(cfg.env); }
  catch (e) { alert("결제 모듈을 불러오지 못했습니다. 잠시 후 다시 시도해주세요."); return; }

  const ordrNo = "elun" + priceKey + Date.now().toString(36) + Math.random().toString(36).slice(2, 6);

  // KCP PC 결제창은 폼(order_info)의 hidden 필드를 읽고, 인증 후 그 폼에 결과(res_cd/enc_data/…)를 채운다.
  const P = {
    site_cd: cfg.siteCd, site_name: cfg.siteName || "Elun",
    pay_method: "100000000000",            // PC 신용카드
    currency: "WON",
    ordr_idxx: ordrNo, good_name: orderName, good_mny: String(amount),
    buyr_mail: email,
    // 인증 결과가 채워질 자리 (KCP가 값 세팅)
    res_cd: "", res_msg: "", enc_data: "", enc_info: "", tran_cd: "", ordr_mony: "",
  };
  const old = document.getElementById("elun-kcp-form");
  if (old) old.remove();
  const form = document.createElement("form");
  form.id = "elun-kcp-form"; form.name = "order_info"; form.method = "post";
  form.style.display = "none";
  Object.keys(P).forEach(function (k) {
    const i = document.createElement("input");
    i.type = "hidden"; i.name = k; i.value = P[k];
    form.appendChild(i);
  });
  document.body.appendChild(form);

  // KCP가 인증 완료 후 호출하는 전역 콜백.
  // ⚠️ 결과는 우리가 만든 order_info 폼이 아니라 **KCP 가 인자로 넘겨주는 자체 폼**
  //    (<form name="KCP_Auth_Hidden">) 에 담겨 온다. 우리 폼은 입력 전용이라 비어 있다.
  //    (2026-08-15: 이 전제를 잘못 잡아 PC 결제가 조용히 실패하던 버그 수정)
  window.m_Completepayment = function (formOrData, closeEvt) {
    try {
      const mine = document.getElementById("elun-kcp-form");
      // 인자가 폼이면 elements 로, 평문 객체면 속성으로, 없으면 우리 폼으로 폴백.
      const get = function (n) {
        if (formOrData) {
          if (formOrData.elements && formOrData.elements[n] != null) {
            const e = formOrData.elements[n];
            return (e && e.value != null) ? e.value : "";
          }
          if (typeof formOrData === "object" && formOrData[n] != null && !formOrData.elements) {
            return String(formOrData[n]);
          }
        }
        const el = mine && mine.querySelector('[name="' + n + '"]');
        return el ? el.value : "";
      };

      const rc = get("res_cd");
      console.log("[ELUN] KCP 콜백 res_cd:", rc, "| res_msg:", get("res_msg"));

      if (rc !== "0000") {
        if (typeof closeEvt === "function") closeEvt();
        // res_cd 가 비어 있어도 반드시 안내한다 — 조용히 사라지면 고객이 문의조차 못 한다.
        alert(rc
          ? ("결제 인증 실패: " + (get("res_msg") || rc))
          : ("결제가 완료되지 않았습니다. 결제창이 정상 종료되지 않았거나 인증이 취소되었습니다.\n"
             + "다시 시도해도 같으면 hello@elun.me 로 주문번호(" + ordrNo + ")와 함께 문의해주세요."));
        return;
      }
      // 서버 승인 요청 (실제 결제 확정 + 위변조 검증은 서버가 KCP 승인 API로)
      fetch(window.ELUN_API_BASE + "/payment/kcp/approve", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          enc_data: get("enc_data"), enc_info: get("enc_info"), tran_cd: get("tran_cd"),
          ordr_no: ordrNo, ordr_mony: String(amount), email: email, product: priceKey,
        }),
      }).then(function (r) {
        return r.ok ? r.json() : r.json().then(function (j) { throw new Error(j.detail || "승인 실패"); });
      }).then(function () {
        if (typeof closeEvt === "function") closeEvt();
        const dest = new URL(opts.redirectTo || "report.html", location.href);
        if (opts.includeOrder !== false) dest.searchParams.set("order", ordrNo);
        dest.searchParams.set("email", email);
        location.href = dest.toString();
      }).catch(function (err) {
        if (typeof closeEvt === "function") closeEvt();
        alert("결제 승인 처리 중 문제가 발생했습니다. 결제가 되었다면 hello@elun.me 로 주문번호(" + ordrNo + ")와 함께 문의해주세요.\n(" + (err.message || err) + ")");
      });
    } catch (e) {
      if (typeof closeEvt === "function") closeEvt();
      alert("결제 처리 오류 — hello@elun.me 로 문의해주세요.");
    }
  };

  try { window.KCP_Pay_Execute_Web(form); }
  catch (e) { /* 정상 종료 시 throw 로 스크립트 종료됨 (KCP 관례) */ }
}

// priceKey: "single" | "decade" | "couple" | "upgrade"
function elunOpenPaddleCheckout(priceKey, opts) {
  if (elunIsKoPage()) {
    if (elunKoReady()) {
      elunOpenKcpCheckout(priceKey, opts);
    } else {
      // 국내 결제 준비 중 게이트 — KRW 표시가와 DS24($) 청구액 불일치 방지.
      // KCP siteCd 가 채워지면(elunKoReady) 이 분기는 자동으로 사라진다.
      alert("국내 결제(카드) 오픈 준비 중입니다 — 며칠 안에 열립니다.\n급하시면 hello@elun.me 로 연락 주세요.");
    }
    return;
  }
  const cfg = window.ELUN_CHECKOUT;
  const pid = cfg && cfg.products && cfg.products[priceKey];
  if (!pid) {
    alert("Checkout isn't configured yet — please email hello@elun.me");
    return;
  }
  // 승인 보류 중에는 결제사로 넘기지 않는다 — 넘기면 DS24 오류 페이지만 보게 된다.
  if (cfg.enabled === false) {
    alert("International checkout is being set up and will open shortly.\n\n"
        + "Email hello@elun.me and we'll send your report as soon as it's live — "
        + "or read the full sample in the meantime.");
    return;
  }
  location.href = "https://www.digistore24.com/product/" + pid;
}

// ── 한국어 페이지 가격 라벨: KCP 활성 시 KRW 교체, 준비 전엔 "결제 준비 중" 표시 ──
// (버튼 id 규약: buybtn=single, buydecadebtn=decade, buycouplebtn=couple)
(function () {
  function won(n) { return n.toLocaleString("ko-KR") + "원"; }
  function apply() {
    if (!elunIsKoPage()) return;
    const ids = ["buybtn", "buydecadebtn", "buycouplebtn", "buyyearbtn"];
    if (elunKoReady()) {
      const a = window.ELUN_CHECKOUT_KO.amounts;
      const map = {
        buybtn: "정밀 리포트 — " + won(a.single),
        buydecadebtn: "리포트 + 대운 10년 — " + won(a.decade),
        buycouplebtn: "두 사람 — " + won(a.couple),
        buyyearbtn: "12개월 정밀 운세 — " + won(a.year),
      };
      for (const id in map) {
        const el = document.getElementById(id);
        if (el) el.textContent = map[id];
      }
    } else {
      // 준비 전: 라벨 뒤에 안내를 붙이고 반투명 처리 (클릭은 위 게이트가 안내 alert)
      for (const id of ids) {
        const el = document.getElementById(id);
        if (!el) continue;
        el.textContent = el.textContent.replace(/\s*—.*$/, "") + " — 결제 준비 중";
        el.style.opacity = "0.55";
        el.setAttribute("aria-disabled", "true");
        el.title = "국내 결제 오픈 준비 중입니다";
      }
    }
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", apply);
  else apply();
})();

// ── 모바일 결제 실패 복귀 배너 (?payerr=사유) ──
// 서버 Ret_URL 처리기가 실패 시 /ko/?payerr=... 로 되돌려보낸다.
(function () {
  function show() {
    let msg;
    try { msg = new URLSearchParams(location.search).get("payerr"); } catch (e) { return; }
    if (!msg) return;
    const bar = document.createElement("div");
    bar.style.cssText = "position:fixed;top:0;left:0;right:0;z-index:99998;background:#3a1512;" +
      "border-bottom:1px solid #d9807a55;color:#f3d9d6;font-size:13.5px;line-height:1.5;" +
      "padding:12px 44px 12px 16px;text-align:center";
    bar.textContent = msg + " — 문제가 계속되면 hello@elun.me 로 알려주세요.";
    const x = document.createElement("button");
    x.textContent = "✕";
    x.style.cssText = "position:absolute;right:10px;top:8px;background:none;border:none;" +
      "color:#f3d9d6;font-size:16px;cursor:pointer;padding:4px";
    x.onclick = function () { bar.remove(); };
    bar.appendChild(x);
    document.body.appendChild(bar);
    // 주소창에서 payerr 제거 (새로고침 시 배너 재출현 방지)
    try {
      const u = new URL(location.href); u.searchParams.delete("payerr");
      history.replaceState(null, "", u.toString());
    } catch (e) {}
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", show);
  else show();
})();
