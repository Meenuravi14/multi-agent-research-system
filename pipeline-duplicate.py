# from agents import build_reader_agent, build_search_agent, writer_chain, critic_chain

# def run_research_pipeline(topic: str)->dict:

#     state = {}

#     print("\n"+"="*50)
#     print("Step 1 - search agent is running...")
#     print("="*50)

#     search_agent = build_search_agent()
#     search_result = search_agent.invoke(
#         {
#             "messages": [("user", f"find recent, reliable and detailed information about: {topic}")]
#         })
#     state["search_results"]=search_result["messages"][-1].content

#     print("\n search result", state["search_results"])

#     print("\n"+"="*50)
#     print("Step 2 - Reader agent is Scraping the top resourses...")
#     print("="*50)

#     reader_agent=build_reader_agent()

#     reader_result = reader_agent.invoke(
#         {
#             "messages": [("user", 
#                           f"based on the following search results about '{topic}',"
#                           f" pick the most relevent URL and scrape it for deeper content.\n\n"
#                           f" search Results: \n {state["search_results"][:800]}")]
#         }
#     )

#     state["scrapped_content"] = reader_result["messages"][-1].content
#     print("\n Scraped Results:", state["scrapped_content"])

#     print("\n"+"="*50)
#     print("Step 3 - writer is drafting the report...")
#     print("="*50)

#     combined_research = (
#         f"SEARCH RESULTS: {state['search_results']}\n"
#         f"SCRAPED CONTENT: {state['scrapped_content']}\n"
#     )

#     state["report"]=writer_chain.invoke(
#         {
#             "topic": topic,
#             "research": combined_research
#         }
#     )

#     print("\n FINAL REPORT\n", state["report"])

#     print("\n"+"="*50)
#     print("Step 4 - Evaluating the report...")
#     print("="*50)

#     state["evaluation"]=critic_chain.invoke({
#         "report": state["report"]
#     })

#     print("\n Critic Report\n", state["evaluation"])

#     return state

# if __name__ == "__main__":
#     topic = input("\n Enter the Research topic: ")
#     run_research_pipeline(topic)





