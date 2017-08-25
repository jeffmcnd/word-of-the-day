drop table if exists words;
create table words (
  id integer primary key autoincrement,
  'text' text not null,
  'date' date
);
