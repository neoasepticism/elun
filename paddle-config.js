// Elun · 체크아웃 단일 정본
//   해외(영문): Digistore24 (2026-07-23 Paddle이 astrology 카테고리 거절 → 전환)
//   국내(/ko/): PortOne V2 → 국내 PG (2026-07-27 통신판매업 신고 완료로 착수)
// 이 파일 하나만 고치면 모든 페이지(index/ko/index, result/ko/result, 리포트 내 업그레이드 CTA)에 반영됩니다.
//
// ⚠️ 파일명(paddle-config.js)과 함수명(elunOpenPaddleCheckout)은 레거시입니다.
//    이미 배포된 리포트 HTML(elun-engine)이 이 파일을 이 이름으로 로드하고 이 함수를 호출하므로,
//    엔진 재배포 없이 결제사를 갈아끼우기 위해 이름을 유지합니다.
//
// 분기 규칙: <html lang="ko"> 이고 ELUN_CHECKOUT_KO 가 설정 완료(PASTE_ 없음)면 포트원,
//            아니면 기존 Digistore24. → 채널키 발급 전까지 한국어 페이지도 DS24 로 폴백.
window.ELUN_CHECKOUT = {
  provider: "digistore24",
  products: {
    single:  "714429",  // Elun Precision Report — $29
    decade:  "714430",  // Elun Precision Report + Decade — $49
    couple:  "714431",  // Elun Compatibility Report — $49
    upgrade: "714432",  // Elun Decade Upgrade — $25
  },
};

// ── 국내 결제 (PortOne V2) ─────────────────────────────────────────────
// 채우는 법 (포트원 콘솔 https://admin.portone.io):
//   1) 결제 연동 → 연동 정보 → Store ID (store-...) → storeId
//   2) 결제 연동 → 채널 관리 → 계약된 PG 채널의 채널 키 (channel-key-...) → channelKey
//   3) 금액을 바꾸면 Railway 의 PORTONE_AMOUNT_* 도 같이 바꿔야 합니다 (서버가 금액 대조로 위변조 차단).
// 서버 연동 규약 (elun-engine server.py — 이미 배포됨):
//   customData = {"product":"single|decade|couple|upgrade"}, customer.email 필수,
//   클레임 주문번호 = paymentId. 웹훅 목적지: https://api.elun.me/webhook/portone
window.ELUN_CHECKOUT_KO = {
  provider: "portone",
  storeId: "PASTE_STORE_ID",
  channelKey: "PASTE_CHANNEL_KEY",
  payMethod: "CARD",            // 채널에 따라 "EASY_PAY" 등으로 변경 가능
  amounts: {                    // KRW — Railway PORTONE_AMOUNT_* 와 반드시 일치
    single:  29000,
    decade:  49000,
    couple:  49000,
    upgrade: 25000,
  },
  orderNames: {
    single:  "Elun 정밀 사주 리포트",
    decade:  "Elun 정밀 리포트 + 대운 10년",
    couple:  "Elun 커플 궁합 리포트",
    upgrade: "Elun 대운 10년 업그레이드",
  },
};

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
  return !!(k && k.storeId && k.storeId.indexOf("PASTE_") !== 0
            && k.channelKey && k.channelKey.indexOf("PASTE_") !== 0);
}

function elunIsKoPage() {
  return (document.documentElement.getAttribute("lang") || "").toLowerCase().indexOf("ko") === 0;
}

// ── 포트원 브라우저 SDK 지연 로드 ──
function elunLoadPortOne() {
  return new Promise(function (resolve, reject) {
    if (window.PortOne) return resolve(window.PortOne);
    const s = document.createElement("script");
    s.src = "https://cdn.portone.io/v2/browser-sdk.js";
    s.onload = function () { window.PortOne ? resolve(window.PortOne) : reject(new Error("PortOne SDK load failed")); };
    s.onerror = function () { reject(new Error("PortOne SDK load failed")); };
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
      '<div style="display:flex;gap:10px;margin-top:16px">' +
      '<button id="elun-email-cancel" style="flex:1;background:transparent;border:1px solid #3a3226;border-radius:24px;color:#b8ab97;padding:11px;font-size:14px;cursor:pointer">취소</button>' +
      '<button id="elun-email-ok" style="flex:2;background:#c9a227;border:none;border-radius:24px;color:#14100b;font-weight:700;padding:11px;font-size:14px;cursor:pointer">결제 계속하기</button>' +
      "</div></div>";
    document.body.appendChild(wrap);
    const input = wrap.querySelector("#elun-email-input");
    const err = wrap.querySelector("#elun-email-err");
    function done(v) { wrap.remove(); resolve(v); }
    function submit() {
      const v = (input.value || "").trim();
      if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(v)) { err.style.display = "block"; input.focus(); return; }
      done(v);
    }
    wrap.querySelector("#elun-email-ok").onclick = submit;
    wrap.querySelector("#elun-email-cancel").onclick = function () { done(null); };
    input.addEventListener("keydown", function (e) { if (e.key === "Enter") submit(); });
    setTimeout(function () { input.focus(); }, 50);
  });
}

// ── 포트원 결제 실행 ──
// opts: { redirectTo: 성공 후 이동(기본 "report.html"), includeOrder: 리다이렉트에 주문번호 포함 여부(기본 true).
//         "upgrade" 는 false — 사용자가 "원래" 주문번호로 재클레임해야 하므로 email 만 프리필. }
async function elunOpenPortOneCheckout(priceKey, opts) {
  opts = opts || {};
  const cfg = window.ELUN_CHECKOUT_KO;
  const amount = cfg.amounts[priceKey];
  const orderName = cfg.orderNames[priceKey] || "Elun Report";
  if (!amount) { alert("결제 설정 오류 — hello@elun.me 로 알려주세요."); return; }

  const email = await elunAskEmail();
  if (!email) return;

  // 클레임 주문번호 = paymentId (서버 규약). 미리 생성해 리다이렉트 URL 에도 굽는다.
  const paymentId = "elun-" + priceKey + "-" + Date.now().toString(36) + "-" + Math.random().toString(36).slice(2, 6);
  const dest = new URL(opts.redirectTo || "report.html", location.href);
  if (opts.includeOrder !== false) dest.searchParams.set("order", paymentId);
  dest.searchParams.set("email", email);
  const destUrl = dest.toString();

  let PortOne;
  try { PortOne = await elunLoadPortOne(); }
  catch (e) { alert("결제 모듈을 불러오지 못했습니다. 잠시 후 다시 시도해주세요."); return; }

  let rsp;
  try {
    rsp = await PortOne.requestPayment({
      storeId: cfg.storeId,
      channelKey: cfg.channelKey,
      paymentId: paymentId,
      orderName: orderName,
      totalAmount: amount,
      currency: "CURRENCY_KRW",
      payMethod: cfg.payMethod || "CARD",
      customer: { email: email },
      customData: { product: priceKey },   // 서버가 이걸로 상품 판별 (SDK 가 JSON 직렬화)
      redirectUrl: destUrl,                // 모바일 리다이렉트 방식 — 실패 시 PG 가 code 파라미터를 덧붙임
    });
  } catch (e) {
    alert("결제가 진행되지 않았습니다. 다시 시도해주세요.");
    return;
  }
  if (rsp && rsp.code != null) {           // PC(iframe) 방식 실패
    if (rsp.code !== "FAILURE_TYPE_PG_CANCEL") alert(rsp.message || "결제에 실패했습니다.");
    return;
  }
  location.href = destUrl;                  // PC 방식 성공 — 웹훅이 원장 기록, 클레임은 API 재조회 폴백도 있음
}

// priceKey: "single" | "decade" | "couple" | "upgrade"
function elunOpenPaddleCheckout(priceKey, opts) {
  if (elunIsKoPage() && elunKoReady()) {
    elunOpenPortOneCheckout(priceKey, opts);
    return;
  }
  const cfg = window.ELUN_CHECKOUT;
  const pid = cfg && cfg.products && cfg.products[priceKey];
  if (!pid) {
    alert("Checkout isn't configured yet — please email hello@elun.me");
    return;
  }
  location.href = "https://www.digistore24.com/product/" + pid;
}

// ── 한국어 페이지 가격 라벨: 포트원 활성 시 KRW 로 교체 ──
// (버튼 id 규약: buybtn=single, buydecadebtn=decade, buycouplebtn=couple)
(function () {
  function won(n) { return n.toLocaleString("ko-KR") + "원"; }
  function apply() {
    if (!(elunIsKoPage() && elunKoReady())) return;
    const a = window.ELUN_CHECKOUT_KO.amounts;
    const map = {
      buybtn: "정밀 리포트 — " + won(a.single),
      buydecadebtn: "리포트 + 대운 10년 — " + won(a.decade),
      buycouplebtn: "두 사람 — " + won(a.couple),
    };
    for (const id in map) {
      const el = document.getElementById(id);
      if (el) el.textContent = map[id];
    }
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", apply);
  else apply();
})();
