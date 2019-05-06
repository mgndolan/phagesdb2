drop table if exists accounts;
create table accounts (
  id integer primary key autoincrement,
  username text not null,
  password text not null,
  firstName text not null,
  lastName text not null,
  studentYear text not null,
  email text not null
);

drop table if exists phages;
create table phages (
  id integer primary key autoincrement,
  phageName text not null,
  phageImage text,
  googleDocImages text,
  foundBy text,
  author text,
  yearFound text,
  cityFound text,
  stateFound text,
  countryFound text,
  gpsLat text,
  gpsLong text,
  soilSample text,
  phageDiscovery text,
  phageNaming text,
  isoTemp text,
  seqCompleted text,
  seqFacility text,
  seqMethod text,
  genomeLength text,
  genomeEnd text,
  overhangLength text,
  overhangSeq text,
  gcContent text,
  cluster text,
  clusterLife text,
  annotateStatus text,
  phageMorph text,
  morphType text,
  phamerated text,
  genBank text,
  genBankLink text,
  archiveStatus text,
  freezerBoxNum text,
  freezerBoxGridNum text,
  fastaFile mediumblob,
  fastqFile mediumblob,
  rawsequenceFile mediumblob,
  extraFile mediumblob
);

--drop table if exists phageHost;
--create table phageHost (
--    phageName text not null,
--    isolationHost text,
--    foreign key (phageName) references phages(phageName)
--);

drop table if exists activityLog;
create table activityLog (
    phageName text not null,
    username text,
    datetime text,
    activity text,
    foreign key (phageName) references phages(phageName),
    foreign key (username) references accounts(username)
);