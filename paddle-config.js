// Elun · Paddle 체크아웃 단일 정본 (cities.js 와 같은 패턴)
// 이 파일 하나만 고치면 모든 페이지(index/ko/index, result/ko/result, 리포트 내 업그레이드 CTA)에 반영됩니다.
//
// 채우는 법:
//   1) Paddle 대시보드 → Developer Tools → Authentication → "Client-side token" 복사 → CLIENT_TOKEN
//   2) Paddle 대시보드 → Catalog → Prices → 상품 4개 각각의 Price ID(pri_로 시작) 복사 → PRICES.*
//   3) 샌드박스에서 테스트할 때만 ENV 를 "sandbox" 로 (그 경우 토큰·price ID 도 샌드박스 전용 값으로 바꿔야 함)
window.ELUN_PADDLE = {
  env: "production", // "sandbox" | "production"
  clientToken: "live_9b5f74b9df87c8e30fe104da711",
  prices: {
    single:  "pri_01ky4mqjxa4fdvfs0jbwhgcggf",  // Precision Report — $29
    decade:  "pri_01ky4ms9z3vxc6ryfbdrnpgjpm",  // Report + Decade — $49
    couple:  "pri_01ky4mt0fngkhqk4h9nxea2pzw",  // Compatibility Report — $49
    upgrade: "pri_01ky4mvxtzp99cxc37ttcctpkq",  // Decade Expansion 업그레이드 — $25
  },
};

// priceKey: "single" | "decade" | "couple" | "upgrade"
// opts: {
//   redirectTo:   결제 성공 후 이동할 페이지 (기본 "report.html")
//   includeOrder: 리다이렉트에 새 주문번호(order)를 포함할지 (기본 true).
//                 "upgrade"처럼 원래 주문에 합쳐지는 결제는 false로 — 새 order id 를 넣으면 안 됨,
//                 사용자가 "원래" 주문번호로 재클레임해야 적용됨(email만 프리필).
//   name:         report.html의 name 필드에 프리필할 값(선택)
// }
function elunOpenPaddleCheckout(priceKey, opts) {
  opts = opts || {};
  const cfg = window.ELUN_PADDLE;
  const priceId = cfg && cfg.prices && cfg.prices[priceKey];
  if (!window.Paddle || !cfg || !cfg.clientToken || cfg.clientToken.indexOf("PASTE_") === 0 || !priceId || priceId.indexOf("PASTE_") === 0) {
    alert("Checkout isn't configured yet — please email hello@elun.me");
    return;
  }
  if (!window.__elunPaddleInit) {
    Paddle.Environment.set(cfg.env);
    Paddle.Initialize({
      token: cfg.clientToken,
      eventCallback: function (event) {
        if (!event || event.name !== "checkout.completed") return;
        const d = event.data || {};
        const txnId = d.transaction_id || (d.transaction && d.transaction.id) || "";
        const email = (d.customer && d.customer.email) || "";
        const dest = (window.__elunPaddleRedirect && window.__elunPaddleRedirect.redirectTo) || "report.html";
        const includeOrder = !window.__elunPaddleRedirect || window.__elunPaddleRedirect.includeOrder !== false;
        const name = (window.__elunPaddleRedirect && window.__elunPaddleRedirect.name) || "";
        const params = new URLSearchParams();
        if (includeOrder && txnId) params.set("order", txnId);
        if (email) params.set("email", email);
        if (name) params.set("name", name);
        const qs = params.toString();
        location.href = dest + (qs ? "?" + qs : "");
      },
    });
    window.__elunPaddleInit = true;
  }
  // eventCallback은 Initialize 시 한 번만 등록되므로, 이번 체크아웃의 리다이렉트 설정을 전역에 잠깐 보관
  window.__elunPaddleRedirect = { redirectTo: opts.redirectTo, includeOrder: opts.includeOrder, name: opts.name };
  Paddle.Checkout.open({ items: [{ priceId: priceId, quantity: 1 }] });
}
