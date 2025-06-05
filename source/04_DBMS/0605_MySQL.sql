-- DCL(계정생성, 권한부여, 권한박탈, 계정삭제)
-- DDL(테이블생성, 테이블삭제, 제약조건, 시퀀스없음)
-- DML(INSERT, UPDATE, DELETE, SELECT)
	-- OUTER JOIN, AND=&&, OR=||, CONCAT 함수를 이용하여 연결연산자 대체
    
show databases; -- database 들 리스트
-- 데이터 베이스로 들어감
use world;
show tables;
select * from city;
desc city;
-- ----------
-- ※ DCL ※
create user user01 identified by 'password'; -- 계정생성
grant all privileges on *.* to user01; -- 권한부여
revoke all privileges on *.* from user01; -- 권한박탈
drop user user01;
-- ------- --
-- DDL ------
-- ------- --
/* MySQL 타입 : nemeric(n), varchar(n), date
정수 : tinyint(1byte), smallint (2byte), mediumint(3byte),
		int/integer(4byte), bigint(8byte)
실수 : float(n, d;4byte), double(n,d;8byte)
문자 : char(n), text, mediumtext(16MB), longtext(4GB)
날짜 : date, datetime, time, year, timestamp
*/

-- DDL이나 DML 명령어는 데이터베이스 내에서 실행
show databases;			-- 데이터베이스 list
create database devdb;	-- 데이터베이스 생성
use devdb; 				-- devdb(특정데이터베이스)로 들어감
select database(); 		-- 현재 들어와 있는 데이터베이스
drop table emp;
drop table if exists emp; -- emp이 존재할 경우 삭제
create table emp(
	empno numeric(4) ,
    ename varchar(6) not null,
    nickname varchar(6) unique,
    sal numeric(7,2) check(sal>0), -- check옵션은 mysql 5.7이하에서는 무시
    comm numeric(7,2) default 0,
    primary key(empno)
);
insert into emp (empno, ename, nickname, sal)
	values(1, '홍길동동동동', '길다길다길어', 1000);
insert into emp (empno, ename, nickname, sal)
	values(1, '홍길동동동동', '길다길다길어', -1);

select * from emp;

-- MySQL에는 시퀀스가 없음
-- MySQL에서 100, 110, 120, ... 을 인위적인 primary key
/*
set @@auto_increment_increment=1;
set @@auto_increment_offset=1;

drop table if exists major;
create table major(
	mcode int primary key auto_increment,
    mname varchar(30),
    moffice varchar(30)
);
insert into major (mname, moffice) values ('컴공','m102호');
insert into major (mname, moffice) values ('ai','m103호');
select * from major;
SELECT @@auto_increment_increment, @@auto_increment_offset;
*/

use devdb;
drop table if exists major;
create table major(
	mcode int primary key auto_increment,
    mname varchar(30),
    moffice varchar(30)
);
insert into major (mname, moffice) values ('컴공','a102호');
insert into major (mname, moffice) values ('ai','a103호');
insert into major (mname, moffice) values ('정보통신','a103호');
select * from major;

drop table if exists student;
create table student(
	sno numeric(4) primary key,
    sname varchar(30) not null,
    mcode int references major(mcode)
);
select * from student;
insert into student values (101, '홍길동', 1);
insert into student values (102, '신길동', 2);
insert into student values (103, '신길동', 3);
insert into student values (104, '오길동', 4);
select *
	from student s, major m
    where s.mcode=m.mcode; -- equi, non-equi, self join은 사용법 동일
select *
	from student s left outer join major m
    on s.mcode=m.mcode; -- outer join

drop table if exists student;
create table student(
	sno numeric(4) ,
    sname varchar(30) not null,
    mcode int,
    primary key(sno),
    foreign key(mcode) references major(mcode)
);
select * from major;
insert into student values (101, '홍길동', 1);
insert into student values (102, '신길동', 2);
insert into student values (103, '신길동', 9); -- 에러: fk
select * from student;
select sno, sname, m.mcode, mname, moffice
	from major m, student s
    where m.mcode = s.mcode; -- 3번 학과는 출력X ( student에 없어서)
select sno, sname, m.mcode, mname, moffice
	from student s right outer join major m
    on s.mcode = m.mcode; -- 3번 학과까지 출력(outer join)

















