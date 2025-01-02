SELECT BP.topic_id, BP.blueprint_id, BP.title, BP.description, TEO.number, TEO.description, ENO.number, ENO.description , U.email, U.name
FROM blueprints BP 
left join terminal_objectives TEO on BP.blueprint_id = TEO.blueprint_id 
left join enabling_objectives ENO on TEO.terminal_objective_id = ENO.terminal_objective_id 
left join topics T on T.topic_id = BP.topic_id
left join users U on U.user_id = T.created_by