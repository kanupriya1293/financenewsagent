Intro to function calling with the Gemini API

Using the Gemini API function calling feature, you can provide custom function definitions to the model. The model doesn't directly invoke these functions, but instead generates structured output that specifies a function name and suggested arguments. You can then use the function name and arguments to call an external API, and you can incorporate the resulting API output into a further query to the model, enabling the model to provide a more comprehensive response and take additional actions.

Function calling empowers users to interact with real-time information and services like databases, customer relationship management systems, and document repositories. The feature also enhances the model's ability to provide relevant and contextual answers. Function calling is best for interacting with external systems. If your use case requires the model to perform computation but doesn't involve external systems or APIs, you should consider using code execution instead.

For a working example of function calling, see the "light bot" notebook.

Beta: The function calling feature is in Beta release. For more information, see the API versions page.
How function calling works
You use the function calling feature by adding structured query data describing programing interfaces, called function declarations, to a model prompt. The function declarations provide the name of the API function, explain its purpose, any parameters it supports, and descriptions of those parameters. After you pass a list of function declarations in a query to the model, it analyzes function declarations and the rest of the query to determine how to use the declared API in response to the request.

The model then returns an object in an OpenAPI compatible schema specifying how to call one or more of the declared functions in order to respond to the user's question. You can then take the recommended function call parameters, call the actual API, get a response, and provide that response to the user or take further action. Note that the model doesn't actually call the declared functions. Instead, you use the returned schema object parameters to call the function. The Gemini API also supports parallel function calling, where the model recommends multiple API function calls based on a single request.

Function declarations
When you implement function calling in a prompt, you create a tools object, which contains one or more function declarations. You define functions using JSON, specifically with a select subset of the OpenAPI schema format. A single function declaration can include the following parameters:

name (string): The unique identifier for the function within the API call.
description (string): A comprehensive explanation of the function's purpose and capabilities.
parameters (object): Defines the input data required by the function.
type (string): Specifies the overall data type, such as object.
properties (object): Lists individual parameters, each with:
type (string): The data type of the parameter, such as string, integer, boolean.
description (string): A clear explanation of the parameter's purpose and expected format.
required (array): An array of strings listing the parameter names that are mandatory for the function to operate.
For code examples of a function declaration using cURL commands, see the Function calling examples. For examples of creating function declarations using the Gemini API SDKs, see the Function calling tutorial.

Best practices for function declarations
Accurately defining your functions is essential when integrating them into your requests. Each function relies on specific parameters that guide its behavior and interaction with the model. The following listing provides guidance on defining the parameters of an individual function in a functions_declarations array.

name: Use clear, descriptive names without space, period (.), or dash (-) characters. Instead, use underscore (_) characters or camel case.

description: Provide detailed, clear, and specific function descriptions, providing examples if necessary. For example, instead of find theaters, use find theaters based on location and optionally movie title that is currently playing in theaters. Avoid overly broad or ambiguous descriptions.

properties > type: Use strongly typed parameters to reduce model hallucinations. For example, if the parameter values are from a finite set, use an enum field instead of listing the values in the description (e.g., "type": "enum", "values": ["now_playing", "upcoming"]). If the parameter value is always an integer, set the type to integer rather than number.

properties > description: Provide concrete examples and constraints. For example, instead of the location to search, use The city and state, e.g. San Francisco, CA or a zip code e.g. 95616.

For more best practices when using function calling, see the Best Practices section.

Function calling mode
You can use the function calling mode parameter to modify the execution behavior of the feature. There are three modes available:

AUTO: The default model behavior. The model decides to predict either a function call or a natural language response.
ANY: The model is constrained to always predict a function call. If allowed_function_names is not provided, the model picks from all of the available function declarations. If allowed_function_names is provided, the model picks from the set of allowed functions.
NONE: The model won't predict a function call. In this case, the model behavior is the same as if you don't pass any function declarations.
The usage of the ANY mode ("forced function calling") is supported for Gemini 1.5 Pro and Gemini 1.5 Flash models only.

You can also pass a set of allowed_function_names that, when provided, limits the functions that the model will call. You should only include allowed_function_names when the mode is ANY. Function names should match function declaration names. With the mode set to ANY and the allowed_function_names set, the model will predict a function call from the set of function names provided.

Key Point: If you set the mode to ANY and provide allowed_function_names, the model picks from the set of allowed functions. If you set the mode to ANY and don't provide allowed_function_names, the model picks from all of the available functions.
The following code snippet from an example request shows how to set the mode to ANY and specify a list of allowed functions:


"tool_config": {
  "function_calling_config": {
    "mode": "ANY",
    "allowed_function_names": ["find_theaters", "get_showtimes"]
  },
}
Function calling examples
This section provides example prompts for function calling using cURL commands. The examples include single turn and multiple-turn scenarios, and enabling different function calling modes.

When using cURL commands with this feature, the function and parameter information is included in the tools element. Each function declaration in the tools element contains the function name, and you specify the parameters using an OpenAPI compatible schema, and a function description.

Single-turn example
Single-turn is when you call the language model one time. With function calling, a single-turn use case might be when you provide the model a natural language query and a list of functions. In this case, the model uses the function declaration, which includes the function name, parameters, and description, to predict which function to call and the arguments to call it with.

The following curl sample is an example of passing in a description of a function that returns information about where a movie is playing. Several function declarations are included in the request, such as find_movies and find_theaters.

Single-turn function calling example request
The response to this curl example might be similar to the following.

Single-turn function calling curl example response
Single-turn example using ANY mode
The following curl example is similar to the single-turn example, but it sets the mode to ANY:


"tool_config": {
  "function_calling_config": {
    "mode": "ANY"
  },
}
Single-turn function calling using ANY mode (request)
The response might be similar to the following:

Single-turn function calling using ANY mode (response)
Single-turn example using ANY mode and allowed functions
The following curl example is similar to the single-turn example, but it sets the mode to ANY and includes a list of allowed functions:


"tool_config": {
  "function_calling_config": {
    "mode": "ANY",
    "allowed_function_names": ["find_theaters", "get_showtimes"]
  },
}
Single-turn function calling using ANY mode and allowed functions (request)
The model can't predict the find_movies function, because it's not on the list of allowed functions, so it predicts a different function instead. The response might be similar to the following:

Single-turn function calling using ANY mode and allowed functions (response)
Multi-turn examples
You can implement a multi-turn function calling scenario by doing the following:

Get a function call response by calling the language model. This is the first turn.
Call the language model using the function call response from the first turn and the function response you get from calling that function. This is the second turn.
The response from the second turn either summarizes the results to answer your query in the first turn, or contains a second function call you can use to get more information for your query.

This topic includes two multi-turn curl examples:

Curl example that uses a function response from a previous turn
Curl example that calls a language model multiple times
Use a response from a previous turn
The following curl sample calls the function and arguments returned by the previous single-turn example to get a response. The method and parameters returned by the single-turn example are in this JSON.


"functionCall": {
  "name": "find_theaters",
  "args": {
    "movie": "Barbie",
    "location": "Mountain View, CA"
  }
}
Multi-turn function calling curl example request
The response to this curl example includes the result of calling the find_theaters method. The response might be similar to the following:

Multi-turn function calling curl example response
Call the model multiple times
The following cURL example calls the generative AI model multiple times to call a function. Each time the model calls the function, it can use a different function to answer a different user query in the request.

Multi-turn function calling curl example request
Multi-turn function calling curl example response
Best practices
Follow these best practices to improve the accuracy and reliability of your function calls.

User prompt
For best results, prepend the user query with the following details:

Additional context for the model. For example, You are a movie API assistant to help users find movies and showtimes based on their preferences.
Details or instructions on how and when to use the functions. For example, Don't make assumptions on showtimes. Always use a future date for showtimes.
Instructions to ask clarifying questions if user queries are ambiguous. For example, Ask clarifying questions if not enough information is available to complete the request.
Sampling parameters
For the temperature parameter, use 0 or another low value. This instructs the model to generate more confident results and reduces hallucinations.

API invocation
If the model proposes the invocation of a function that would send an order, update a database, or otherwise have significant consequences, validate the function call with the user before executing it.