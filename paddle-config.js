// Elun · 체크아웃 단일 정본 — 현재 결제사: Digistore24 (2026-07-23 Paddle이 astrology 카테고리 거절 → 전환)
// 이 파일 하나만 고치면 모든 페이지(index/ko/index, result/ko/result, 리포트 내 업그레이드 CTA)에 반영됩니다.
//
// ⚠️ 파일명(paddle-config.js)과 함수명(elunOpenPaddleCheckout)은 레거시입니다.
//    이미 배포된 리포트 HTML(elun-engine)이 이 파일을 이 이름으로 로드하고 이 함수를 호출하므로,
//    엔진 재배포 없이 결제사를 갈아끼우기 위해 이름을 유지합니다. 내용물만 Digistore24 입니다.
//
// 채우는 법:
//   Digistore24 대시보드 → My products → Product list → 각 상품의 Product ID 를 PRODUCTS.* 에.
//   체크아웃은 https://www.digistore24.com/product/{ID} 호스티드 주문폼으로 리다이렉트됩니다.
//   결제 완료 후 Digistore24가 상품별 Thank you page(대시보드에서 설정)로 order_id·email 을 붙여 보냅니다.
window.ELUN_CHECKOUT = {
  provider: "digistore24",
  products: {
    single:  "714429",  // Elun Precision Report — $29
    decade:  "714430",  // Elun Precision Report + Decade — $49
    couple:  "714431",  // Elun Compatibility Report — $49
    upgrade: "714432",  // Elun Decade Upgrade — $25
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

// priceKey: "single" | "decade" | "couple" | "upgrade"
// opts 는 레거시 시그니처 호환용으로 받기만 합니다 — 결제 후 이동(Thank you page)은
// Digistore24 상품 설정에서 정해지므로 여기서 redirectTo 를 제어하지 않습니다.
function elunOpenPaddleCheckout(priceKey, opts) {
  const cfg = window.ELUN_CHECKOUT;
  const pid = cfg && cfg.products && cfg.products[priceKey];
  if (!pid) {
    alert("Checkout isn't configured yet — please email hello@elun.me");
    return;
  }
  location.href = "https://www.digistore24.com/product/" + pid;
}
