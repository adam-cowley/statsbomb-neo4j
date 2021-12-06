import { config } from 'dotenv'
import { gql, ApolloServer } from "apollo-server"
import { Neo4jGraphQL } from "@neo4j/graphql"
import neo4j from "neo4j-driver"

config()



import { typeDefs } from './schema'


const driver = neo4j.driver(
  process.env.NEO4J_URI!,
  neo4j.auth.basic(process.env.NEO4J_USER!, process.env.NEO4J_PASSWORD!)
);

const neoSchema = new Neo4jGraphQL({ typeDefs, driver });

const server = new ApolloServer({
  schema: neoSchema.schema,
});

server.listen().then(({ url }) => {
  console.log(`GraphQL server ready on ${url}`);
});
