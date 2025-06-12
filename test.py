from selenium import webdriver

# Khởi tạo trình duyệt (ví dụ với Chrome)
driver = webdriver.Chrome()

# Mở trang web
driver.get("https://example.com")

# Thực thi mã JavaScript với Selenium
driver.execute_script("""
const mt = document.createElement('div');
mt.setAttribute('id', 'huydev');
mt.style.cssText = `
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgb(255 204 204 / 89%);
    z-index: 20000;
    display: flex;
    justify-content: center;
    align-items: center;
    font-size: 70pt;
    color: #a00000;
`;

const span = document.createElement('span');
span.style.animation = 'blink 1s infinite';
span.textContent = 'ERROR';
mt.appendChild(span);

const style = document.createElement('style');
style.innerHTML = `
@keyframes blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0; }
}
`;
document.head.appendChild(style);
document.body.appendChild(mt);
""")
