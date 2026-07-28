// Elun · 생년월일 분리 입력 컴포넌트 (연/월/일 세그먼트 + 자동 포커스 이동)
// 브라우저 기본 <input type="date">는 세그먼트 이동 동작을 제어할 수 없어(데스크톱·모바일 제각각),
// 세 칸 분리 입력으로 교체한다. 기존 코드 호환: 원본 input을 hidden으로 바꾸고
// value getter/setter를 instance-level로 재정의 → 기존 프리필(.value=iso)·제출(.value 읽기) 코드 무수정.
//
// 사용: elunDateSeg('bdate', {y:'연도', m:'월', d:'일', next:'btime'})
//   next: 일(day) 입력이 끝나면 포커스를 넘길 다음 필드 id (선택)
function elunDateSeg(id, opts) {
  opts = opts || {};
  var orig = document.getElementById(id);
  if (!orig || orig.dataset.segged) return;
  orig.dataset.segged = "1";

  var wrap = document.createElement("div");
  wrap.className = "dseg";
  wrap.style.cssText = "display:flex;gap:8px";
  function seg(ph, maxlen, flex, auto) {
    var i = document.createElement("input");
    i.type = "text";
    i.inputMode = "numeric";
    i.autocomplete = auto || "off";
    i.placeholder = ph;
    i.maxLength = maxlen;
    i.required = true;
    i.setAttribute("pattern", "[0-9]*");
    i.style.cssText = "flex:" + flex + ";min-width:0;text-align:center";
    return i;
  }
  var Y = seg(opts.y || "YYYY", 4, "1.6", "bday-year");
  var M = seg(opts.m || "MM", 2, "1", "bday-month");
  var D = seg(opts.d || "DD", 2, "1", "bday-day");
  wrap.appendChild(Y); wrap.appendChild(M); wrap.appendChild(D);

  orig.parentNode.insertBefore(wrap, orig);
  orig.type = "hidden";
  orig.required = false;

  function pad2(v) { return v.length === 1 ? "0" + v : v; }
  function nextOf(el) { return el === Y ? M : el === M ? D : (opts.next ? document.getElementById(opts.next) : null); }
  function prevOf(el) { return el === D ? M : el === M ? Y : null; }

  function wire(el) {
    el.addEventListener("input", function () {
      var v = el.value.replace(/\D/g, "");
      // 한 자리로 확정되는 값은 즉시 0패딩 후 이동 (월 2-9, 일 4-9)
      if (el === M && v.length === 1 && +v >= 2) v = "0" + v;
      if (el === D && v.length === 1 && +v >= 4) v = "0" + v;
      // 범위 클램프
      if (el === M && v.length === 2) { var m = +v; if (m < 1) v = "01"; if (m > 12) v = "12"; }
      if (el === D && v.length === 2) { var d = +v; if (d < 1) v = "01"; if (d > 31) v = "31"; }
      el.value = v;
      if (v.length >= el.maxLength) {
        var nx = nextOf(el);
        if (nx && !nx.disabled) { nx.focus(); if (nx.select) nx.select(); }
      }
    });
    el.addEventListener("keydown", function (e) {
      if (e.key === "Backspace" && el.value === "") {
        var pv = prevOf(el);
        if (pv) { e.preventDefault(); pv.focus(); }
      }
    });
    el.addEventListener("blur", function () {
      if (el !== Y && el.value.length === 1) el.value = pad2(el.value);
    });
  }
  wire(Y); wire(M); wire(D);

  // 붙여넣기: 연도 칸에 1990-08-21 / 19900821 등을 통째로 넣는 경우 분배
  Y.addEventListener("paste", function (e) {
    var t = (e.clipboardData || window.clipboardData).getData("text").replace(/\D/g, "");
    if (t.length === 8) {
      e.preventDefault();
      Y.value = t.slice(0, 4); M.value = t.slice(4, 6); D.value = t.slice(6, 8);
      var nx = opts.next ? document.getElementById(opts.next) : null;
      if (nx && !nx.disabled) nx.focus();
    }
  });

  // 기존 코드 호환 — .value 로 yyyy-mm-dd 읽기/쓰기
  Object.defineProperty(orig, "value", {
    configurable: true,
    get: function () {
      if (Y.value.length === 4 && M.value.length >= 1 && D.value.length >= 1)
        return Y.value + "-" + pad2(M.value) + "-" + pad2(D.value);
      return "";
    },
    set: function (v) {
      var m = /^(\d{4})-(\d{1,2})-(\d{1,2})/.exec(v || "");
      if (m) { Y.value = m[1]; M.value = pad2(m[2]); D.value = pad2(m[3]); }
      else { Y.value = M.value = D.value = ""; }
    },
  });
}
