// 2.js
/* 동적인 부분 */
var name = prompt("이름은?", "홍길동"); // 취소 클릭시 'null' 리턴
if (name != 'null' && name != '') { // 입력후 확인 클릭시
    document.write(name + '님 반갑습니다<br>');
}