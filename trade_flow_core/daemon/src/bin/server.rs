use std::collections::HashMap;
use std::fs;
use std::path::PathBuf;
use std::sync::{Arc, Mutex};

use actix_web::{web, App, HttpResponse, HttpServer, Responder};
use serde::{Deserialize, Serialize};
use log::{info, error};
use tokio::task;

// Constants
const TRADE_FLOW_SERVER_PORT: u16 = 9165;

// Struct to hold the server state
struct ServerState {
    basedir: PathBuf,
    flows: Arc<Mutex<HashMap<String, Flow>>>,
    task_manager: TaskManager,
}

// Flow struct placeholder (to be implemented)
#[derive(Serialize, Deserialize)]
struct Flow {
    name: String,
}

impl Flow {
    fn from_file(flow: &str) -> Result<Flow, String> {
        // Implement reading from a file and creating Flow
        Ok(Flow {
            name: flow.to_string(),
        })
    }
}

// TaskManager placeholder (to be implemented)
struct TaskManager;

impl TaskManager {
    fn new() -> Self {
        TaskManager
    }

    fn start_process_in_thread<F>(&self, task_name: &str, target_function: F)
    where
        F: FnOnce() + Send + 'static,
    {
        // Use tokio::spawn or similar to create tasks
        task::spawn(target_function);
    }

    fn stop_process(&self, _task_name: &str) -> bool {
        // Implement task stopping logic
        true
    }

    fn list_tasks(&self) -> HashMap<String, String> {
        // Implement logic to list all running tasks
        HashMap::new()
    }
}

// Helper function to create basedir based on OS
fn get_basedir() -> PathBuf {
    match std::env::consts::OS {
        "windows" => PathBuf::from(format!("{}/trade_flow", std::env::var("USERPROFILE").unwrap())),
        "linux" | "macos" => {
            let home = std::env::var("XDG_STATE_HOME").unwrap_or(std::env::var("HOME").unwrap());
            PathBuf::from(format!("{}/.trade_flow", home))
        }
        _ => panic!("Unsupported operating system"),
    }
}

// Routes for the Actix web server

async fn healthy() -> impl Responder {
    HttpResponse::Ok().body("trade_flow is healthy")
}

async fn environments_available(data: web::Data<ServerState>) -> impl Responder {
    // Sample response placeholder (real implementation should load environments)
    let environments = vec![
        ("env1", "Description 1", "v1.0"),
        ("env2", "Description 2", "v1.1"),
    ];
    HttpResponse::Ok().json(environments)
}

async fn start_task(
    data: web::Data<ServerState>,
    web::Path((task_name, target_function_name)): web::Path<(String, String)>,
) -> impl Responder {
    // Example of starting a task (real function needs to be invoked)
    let server_state = data.into_inner();
    let task_manager = &server_state.task_manager;

    task_manager.start_process_in_thread(&task_name, || {
        println!("Task {} started!", task_name);
    });

    HttpResponse::Ok().body(format!("Task '{}' started successfully.", task_name))
}

async fn stop_task(
    data: web::Data<ServerState>,
    web::Path(task_name): web::Path<String>,
) -> impl Responder {
    let server_state = data.into_inner();
    let task_manager = &server_state.task_manager;

    if task_manager.stop_process(&task_name) {
        HttpResponse::Ok().body(format!("Task '{}' stopped successfully.", task_name))
    } else {
        HttpResponse::Ok().body(format!("Failed to stop task '{}'.", task_name))
    }
}

// Main function to start the server
#[actix_web::main]
async fn main() -> std::io::Result<()> {
    // Initialize logging
    env_logger::init();

    let basedir = get_basedir();
    let server_state = web::Data::new(ServerState {
        basedir,
        flows: Arc::new(Mutex::new(HashMap::new())),
        task_manager: TaskManager::new(),
    });

    info!("Started server");

    HttpServer::new(move || {
        App::new()
            .app_data(server_state.clone())
            .route("/healthy", web::get().to(healthy))
            .route("/environments", web::get().to(environments_available))
            .route("/start_task/{task_name}/{target_function_name}", web::post().to(start_task))
            .route("/stop_task/{task_name}", web::post().to(stop_task))
    })
    .bind(("0.0.0.0", TRADE_FLOW_SERVER_PORT))?
    .run()
    .await
}
