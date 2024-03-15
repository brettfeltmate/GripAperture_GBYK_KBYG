/*
  * SQL commands to create experiment databases. 
  */

CREATE TABLE participants (
    id integer primary key autoincrement not null,
    userhash text not null,
    gender text not null,
    age integer not null, 
    handedness text not null,
    created text not null
);

CREATE TABLE trials (
    id integer primary key autoincrement not null,
    participant_id integer not null references participants(id),
    practicing text not null,
    block_num integer not null,
    trial_num integer not null,
    task_type text not null,
    target_size text not null,
    target_loc text not null,
    distractor_size text not null,
    distractor_loc text not null,
    response_time text not null,
    movement_time text not null,
    reach_completed text not null
);
