import React from 'react';
import { useQuery } from 'react-apollo';
import { gql } from 'apollo-boost';

const QUERY_USERS = gql`
  query {
    users {
      id
      firstName
      lastName
    }
}
`;
export default function UserInfo() {
  // Polling: provides near-real-time synchronization with
  // your server by causing a query to execute periodically
  // at a specified interval
  const { data, loading } = useQuery(
    QUERY_USERS, {
      pollInterval: 50000 // refetch the result every x second
    }
  );

  // should handle loading status
  if (loading) return <p>Loading...</p>;

  return data.users.map(({ id, firstName, lastName }) => (
    <div key={id}>
      <p>
        User - {id}: {firstName} {lastName}
      </p>
    </div>
  ));
}
