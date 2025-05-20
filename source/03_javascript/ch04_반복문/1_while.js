/* while(조건){
    반복할 명령어들;
}
    do{
        반복할 명령어들;
    }while(조건);
    1초동안 while문을 몇번 실행했는지 출력
    */
var now = new Date();
var startTime = now.getTime();
// console.log(startTime);
var cnt = 0;
while (new Date().getTime() < startTime + 1000) {
  cnt++; // cnt 1증가
}
console.log("while문 반복횟수:", cnt);

startTime = new Date().getTime();
cnt = 0;
do {
  ++cnt;
} while (new Date().getTime() < startTime + 1000);
console.log("do~while문 반복 횟수 :", cnt);
